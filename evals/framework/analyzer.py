"""Statistical analyzer for evaluation results.

This module computes win rates, pairwise preferences, confidence intervals,
and Bradley-Terry rankings from collected human judgments.
"""

import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from .schemas import (
    WinRateResult,
    PairwiseResult,
    BradleyTerryResult,
)
from db.eval_db import EvalDatabase

logger = logging.getLogger(__name__)


class EvalAnalyzer:
    """Analyzes evaluation results with statistical methods."""

    def __init__(self, db: EvalDatabase):
        """Initialize the analyzer.

        Args:
            db: Database containing evaluation data
        """
        self.db = db

    def compute_win_rates(self, stage_id: str) -> List[WinRateResult]:
        """Compute win rate per model for a stage.

        Win rate = (number of wins) / (number of appearances)

        Args:
            stage_id: Stage to analyze

        Returns:
            List of WinRateResult sorted by win rate descending
        """
        stats = self.db.get_model_stats(stage_id)

        results = []
        for model_id, counts in stats.items():
            wins = counts["wins"]
            appearances = counts["appearances"]
            win_rate = wins / appearances if appearances > 0 else 0.0

            results.append(WinRateResult(
                model_id=model_id,
                stage_id=stage_id,
                wins=wins,
                appearances=appearances,
                win_rate=win_rate,
            ))

        # Sort by win rate descending
        results.sort(key=lambda x: x.win_rate, reverse=True)

        logger.info(
            f"Win rates for {stage_id}: "
            f"{[(r.model_id, f'{r.win_rate:.1%}') for r in results]}"
        )

        return results

    def pairwise_preference(
        self,
        stage_id: str,
        model_a: str,
        model_b: str,
    ) -> PairwiseResult:
        """Compute pairwise preference probability between two models.

        Uses binomial test to determine if preference is statistically significant.

        Args:
            stage_id: Stage to analyze
            model_a: First model ID
            model_b: Second model ID

        Returns:
            PairwiseResult with preference probability and significance
        """
        try:
            from scipy.stats import binomtest
        except ImportError:
            logger.warning("scipy not available, using approximate CI")
            return self._pairwise_preference_approx(stage_id, model_a, model_b)

        head_to_head = self.db.get_head_to_head(stage_id, model_a, model_b)

        a_wins = sum(1 for h in head_to_head if h["winner"] == model_a)
        b_wins = sum(1 for h in head_to_head if h["winner"] == model_b)
        total = len(head_to_head)

        if total == 0:
            return PairwiseResult(
                model_a=model_a,
                model_b=model_b,
                stage_id=stage_id,
                a_wins=0,
                b_wins=0,
                total=0,
                p_a_preferred=0.5,
                p_value=1.0,
                ci_low=0.0,
                ci_high=1.0,
                significant=False,
            )

        # Binomial test: H0 is p = 0.5
        result = binomtest(a_wins, total, p=0.5, alternative="two-sided")
        p_hat = a_wins / total
        ci = result.proportion_ci(confidence_level=0.95)

        # Significant if 95% CI doesn't include 0.5
        significant = ci.low > 0.5 or ci.high < 0.5

        pairwise = PairwiseResult(
            model_a=model_a,
            model_b=model_b,
            stage_id=stage_id,
            a_wins=a_wins,
            b_wins=b_wins,
            total=total,
            p_a_preferred=p_hat,
            p_value=result.pvalue,
            ci_low=ci.low,
            ci_high=ci.high,
            significant=significant,
        )

        logger.info(
            f"Pairwise {model_a} vs {model_b}: "
            f"P(A>B)={p_hat:.2f}, p={result.pvalue:.3f}, "
            f"CI=[{ci.low:.2f}, {ci.high:.2f}], sig={significant}"
        )

        return pairwise

    def _pairwise_preference_approx(
        self,
        stage_id: str,
        model_a: str,
        model_b: str,
    ) -> PairwiseResult:
        """Approximate pairwise preference without scipy."""
        import math

        head_to_head = self.db.get_head_to_head(stage_id, model_a, model_b)

        a_wins = sum(1 for h in head_to_head if h["winner"] == model_a)
        b_wins = sum(1 for h in head_to_head if h["winner"] == model_b)
        total = len(head_to_head)

        if total == 0:
            return PairwiseResult(
                model_a=model_a,
                model_b=model_b,
                stage_id=stage_id,
                a_wins=0,
                b_wins=0,
                total=0,
                p_a_preferred=0.5,
                p_value=1.0,
                ci_low=0.0,
                ci_high=1.0,
                significant=False,
            )

        p_hat = a_wins / total

        # Wilson score interval for 95% CI
        z = 1.96
        denominator = 1 + z**2 / total
        center = (p_hat + z**2 / (2 * total)) / denominator
        spread = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * total)) / total) / denominator

        ci_low = max(0, center - spread)
        ci_high = min(1, center + spread)

        significant = ci_low > 0.5 or ci_high < 0.5

        return PairwiseResult(
            model_a=model_a,
            model_b=model_b,
            stage_id=stage_id,
            a_wins=a_wins,
            b_wins=b_wins,
            total=total,
            p_a_preferred=p_hat,
            p_value=0.0,  # Not computed without scipy
            ci_low=ci_low,
            ci_high=ci_high,
            significant=significant,
        )

    def all_pairwise_comparisons(
        self, stage_id: str
    ) -> List[PairwiseResult]:
        """Compute all pairwise comparisons for a stage.

        Args:
            stage_id: Stage to analyze

        Returns:
            List of PairwiseResult for all model pairs
        """
        stats = self.db.get_model_stats(stage_id)
        models = list(stats.keys())

        results = []
        for i, model_a in enumerate(models):
            for model_b in models[i + 1:]:
                result = self.pairwise_preference(stage_id, model_a, model_b)
                results.append(result)

        return results

    def bradley_terry_ranking(
        self,
        stage_id: str,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
    ) -> List[BradleyTerryResult]:
        """Fit Bradley-Terry model and rank models by strength.

        The Bradley-Terry model estimates latent strength parameters θ_m
        such that P(m > n) = exp(θ_m) / (exp(θ_m) + exp(θ_n)).

        Args:
            stage_id: Stage to analyze
            max_iterations: Maximum iterations for convergence
            tolerance: Convergence tolerance

        Returns:
            List of BradleyTerryResult sorted by strength descending
        """
        pairwise_data = self.db.get_all_pairwise(stage_id)

        if not pairwise_data:
            logger.warning(f"No pairwise data for stage {stage_id}")
            return []

        # Get all models
        models = list(set(
            [d["winner"] for d in pairwise_data] +
            [d["loser"] for d in pairwise_data]
        ))

        if len(models) < 2:
            logger.warning("Need at least 2 models for Bradley-Terry")
            return []

        # Initialize strengths
        theta = {m: 1.0 for m in models}

        # Count wins per model
        wins = defaultdict(int)
        for d in pairwise_data:
            wins[d["winner"]] += 1

        # Iterative algorithm
        for iteration in range(max_iterations):
            old_theta = theta.copy()
            new_theta = {}

            for m in models:
                # Numerator: number of wins
                num = wins[m]

                # Denominator: sum of 1/(θ_m + θ_opponent) for all comparisons
                denom = 0.0
                for d in pairwise_data:
                    if d["winner"] == m:
                        denom += 1.0 / (theta[m] + theta[d["loser"]])
                    elif d["loser"] == m:
                        denom += 1.0 / (theta[m] + theta[d["winner"]])

                new_theta[m] = num / denom if denom > 0 else 1.0

            # Normalize to prevent drift
            total = sum(new_theta.values())
            theta = {m: v / total * len(models) for m, v in new_theta.items()}

            # Check convergence
            max_change = max(abs(theta[m] - old_theta[m]) for m in models)
            if max_change < tolerance:
                logger.info(f"Bradley-Terry converged in {iteration + 1} iterations")
                break

        # Build results sorted by strength
        results = []
        sorted_models = sorted(models, key=lambda m: theta[m], reverse=True)
        for rank, model in enumerate(sorted_models, 1):
            results.append(BradleyTerryResult(
                model_id=model,
                stage_id=stage_id,
                strength=theta[model],
                rank=rank,
            ))

        logger.info(
            f"Bradley-Terry ranking for {stage_id}: "
            f"{[(r.model_id, f'{r.strength:.3f}') for r in results]}"
        )

        return results

    def compute_mean_scores(
        self,
        stage_id: str,
    ) -> Dict[str, Dict[str, float]]:
        """Compute mean scores per model per criterion.

        Args:
            stage_id: Stage to analyze

        Returns:
            Dict mapping model_id -> {criterion: mean_score}
        """
        judgments = self.db.get_judgments_for_stage(stage_id)

        # Accumulate scores
        score_sums: Dict[str, Dict[str, List[int]]] = defaultdict(
            lambda: defaultdict(list)
        )

        for j in judgments:
            if j["scores"]:
                model = j["winner_model_id"]
                for criterion, score in j["scores"].items():
                    score_sums[model][criterion].append(score)

        # Compute means
        results = {}
        for model, criteria in score_sums.items():
            results[model] = {
                criterion: sum(scores) / len(scores)
                for criterion, scores in criteria.items()
            }

        return results

    def compute_tag_frequencies(
        self,
        stage_id: str,
    ) -> Dict[str, Dict[str, int]]:
        """Compute tag frequencies per model.

        Args:
            stage_id: Stage to analyze

        Returns:
            Dict mapping model_id -> {tag: count}
        """
        judgments = self.db.get_judgments_for_stage(stage_id)

        tag_counts: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for j in judgments:
            if j["tags"]:
                model = j["winner_model_id"]
                for tag in j["tags"]:
                    tag_counts[model][tag] += 1

        return dict(tag_counts)

    def generate_report(self, stage_id: str) -> Dict:
        """Generate a comprehensive analysis report for a stage.

        Args:
            stage_id: Stage to analyze

        Returns:
            Dict containing all analysis results
        """
        return {
            "stage_id": stage_id,
            "win_rates": [r.to_dict() for r in self.compute_win_rates(stage_id)],
            "pairwise_comparisons": [
                r.to_dict() for r in self.all_pairwise_comparisons(stage_id)
            ],
            "bradley_terry": [
                r.to_dict() for r in self.bradley_terry_ranking(stage_id)
            ],
            "mean_scores": self.compute_mean_scores(stage_id),
            "tag_frequencies": self.compute_tag_frequencies(stage_id),
        }
