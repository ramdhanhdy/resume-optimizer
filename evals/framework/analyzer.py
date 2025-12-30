"""Statistical analyzer for evaluation results.

This module computes win rates, pairwise preferences, confidence intervals,
and Bradley-Terry rankings from collected human judgments.
"""

import logging
import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any

from .schemas import (
    WinRateResult,
    PairwiseResult,
    BradleyTerryResult,
)
from db.eval_db import EvalDatabase

logger = logging.getLogger(__name__)

# Module-level scipy import (optimization #5)
try:
    from scipy.stats import binomtest
    _HAS_SCIPY = True
except ImportError:
    binomtest = None
    _HAS_SCIPY = False


class EvalAnalyzer:
    """Analyzes evaluation results with statistical methods."""

    def __init__(self, db: EvalDatabase):
        """Initialize the analyzer.

        Args:
            db: Database containing evaluation data
        """
        self.db = db
        # Stage-level caches (optimization #1b, #1c)
        self._judgments_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._stats_cache: Dict[str, Dict[str, Dict[str, int]]] = {}
        self._head_to_head_cache: Dict[str, Dict[tuple, Dict[str, int]]] = {}

    def clear_cache(self, stage_id: Optional[str] = None) -> None:
        """Clear cached data for a stage or all stages.

        Args:
            stage_id: Stage to clear, or None to clear all
        """
        if stage_id is None:
            self._judgments_cache.clear()
            self._stats_cache.clear()
            self._head_to_head_cache.clear()
        else:
            self._judgments_cache.pop(stage_id, None)
            self._stats_cache.pop(stage_id, None)
            self._head_to_head_cache.pop(stage_id, None)

    def _get_judgments(self, stage_id: str) -> List[Dict[str, Any]]:
        """Get judgments for a stage with caching."""
        if stage_id not in self._judgments_cache:
            self._judgments_cache[stage_id] = self.db.get_judgments_for_stage(stage_id)
        return self._judgments_cache[stage_id]

    def _get_model_stats(self, stage_id: str) -> Dict[str, Dict[str, int]]:
        """Get model stats for a stage with caching."""
        if stage_id not in self._stats_cache:
            self._stats_cache[stage_id] = self.db.get_model_stats(stage_id)
        return self._stats_cache[stage_id]

    def _get_head_to_head_counts(self, stage_id: str) -> Dict[tuple, Dict[str, int]]:
        """Get all head-to-head counts for a stage with caching."""
        if stage_id not in self._head_to_head_cache:
            self._head_to_head_cache[stage_id] = self.db.get_all_head_to_head_counts(stage_id)
        return self._head_to_head_cache[stage_id]

    def compute_win_rates(
        self,
        stage_id: str,
        stats: Optional[Dict[str, Dict[str, int]]] = None,
    ) -> List[WinRateResult]:
        """Compute win rate per model for a stage.

        Win rate = (number of wins) / (number of appearances)

        Args:
            stage_id: Stage to analyze
            stats: Pre-fetched model stats (optional, for batch operations)

        Returns:
            List of WinRateResult sorted by win rate descending
        """
        if stats is None:
            stats = self._get_model_stats(stage_id)

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

        # Deferred logging (optimization #4)
        if logger.isEnabledFor(logging.INFO):
            logger.info(
                "Win rates for %s: %s",
                stage_id,
                [(r.model_id, f"{r.win_rate:.1%}") for r in results],
            )

        return results

    def pairwise_preference(
        self,
        stage_id: str,
        model_a: str,
        model_b: str,
        head_to_head_counts: Optional[Dict[tuple, Dict[str, int]]] = None,
    ) -> PairwiseResult:
        """Compute pairwise preference probability between two models.

        Uses binomial test to determine if preference is statistically significant.

        Args:
            stage_id: Stage to analyze
            model_a: First model ID
            model_b: Second model ID
            head_to_head_counts: Pre-fetched counts (optional, for batch operations)

        Returns:
            PairwiseResult with preference probability and significance
        """
        # Get counts from cache or pre-fetched data
        if head_to_head_counts is not None:
            pair_key = tuple(sorted([model_a, model_b]))
            counts = head_to_head_counts.get(pair_key, {})
            a_wins = counts.get(model_a, 0)
            b_wins = counts.get(model_b, 0)
            total = counts.get("total", 0)
        else:
            # Fallback to individual DB query for ad-hoc calls
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

        # Use scipy if available, otherwise approximate (optimization #5)
        if not _HAS_SCIPY:
            return self._compute_pairwise_approx(
                model_a, model_b, stage_id, a_wins, b_wins, total, p_hat
            )

        # Binomial test: H0 is p = 0.5
        result = binomtest(a_wins, total, p=0.5, alternative="two-sided")
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

        # Deferred logging at DEBUG level for batch operations (optimization #4)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Pairwise %s vs %s: P(A>B)=%.2f, p=%.3f, CI=[%.2f, %.2f], sig=%s",
                model_a, model_b, p_hat, result.pvalue, ci.low, ci.high, significant,
            )

        return pairwise

    def _compute_pairwise_approx(
        self,
        model_a: str,
        model_b: str,
        stage_id: str,
        a_wins: int,
        b_wins: int,
        total: int,
        p_hat: float,
    ) -> PairwiseResult:
        """Compute pairwise result with Wilson score CI (no scipy)."""
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

    def _pairwise_preference_approx(
        self,
        stage_id: str,
        model_a: str,
        model_b: str,
    ) -> PairwiseResult:
        """Approximate pairwise preference without scipy (legacy ad-hoc method)."""
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
        return self._compute_pairwise_approx(
            model_a, model_b, stage_id, a_wins, b_wins, total, p_hat
        )

    def all_pairwise_comparisons(
        self,
        stage_id: str,
        stats: Optional[Dict[str, Dict[str, int]]] = None,
        head_to_head_counts: Optional[Dict[tuple, Dict[str, int]]] = None,
    ) -> List[PairwiseResult]:
        """Compute all pairwise comparisons for a stage.

        Uses bulk head-to-head counts to avoid N^2 DB queries (optimization #1a).

        Args:
            stage_id: Stage to analyze
            stats: Pre-fetched model stats (optional)
            head_to_head_counts: Pre-fetched head-to-head counts (optional)

        Returns:
            List of PairwiseResult for all model pairs
        """
        if stats is None:
            stats = self._get_model_stats(stage_id)
        if head_to_head_counts is None:
            head_to_head_counts = self._get_head_to_head_counts(stage_id)

        models = list(stats.keys())

        results = []
        for i, model_a in enumerate(models):
            for model_b in models[i + 1:]:
                result = self.pairwise_preference(
                    stage_id, model_a, model_b, head_to_head_counts
                )
                results.append(result)

        return results

    def bradley_terry_ranking(
        self,
        stage_id: str,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
        pairwise_data: Optional[List[Dict[str, Any]]] = None,
    ) -> List[BradleyTerryResult]:
        """Fit Bradley-Terry model and rank models by strength.

        The Bradley-Terry model estimates latent strength parameters θ_m
        such that P(m > n) = exp(θ_m) / (exp(θ_m) + exp(θ_n)).

        Uses adjacency maps and integer indices for O(models * unique_opponents)
        per iteration instead of O(models * total_rows) (optimization #2).

        Args:
            stage_id: Stage to analyze
            max_iterations: Maximum iterations for convergence
            tolerance: Convergence tolerance
            pairwise_data: Pre-fetched pairwise data (optional)

        Returns:
            List of BradleyTerryResult sorted by strength descending
        """
        if pairwise_data is None:
            pairwise_data = self.db.get_all_pairwise(stage_id)

        if not pairwise_data:
            logger.warning("No pairwise data for stage %s", stage_id)
            return []

        # Get all models and create index mapping (optimization #2b)
        models = list(set(
            [d["winner"] for d in pairwise_data] +
            [d["loser"] for d in pairwise_data]
        ))

        if len(models) < 2:
            logger.warning("Need at least 2 models for Bradley-Terry")
            return []

        n_models = len(models)
        model_to_idx = {m: i for i, m in enumerate(models)}
        idx_to_model = {i: m for m, i in model_to_idx.items()}

        # Build adjacency map with counts (optimization #2a)
        # opponents[i][j] = count of comparisons between model i and model j
        opponents: List[Dict[int, int]] = [defaultdict(int) for _ in range(n_models)]
        wins = [0] * n_models

        for d in pairwise_data:
            w_idx = model_to_idx[d["winner"]]
            l_idx = model_to_idx[d["loser"]]
            wins[w_idx] += 1
            opponents[w_idx][l_idx] += 1
            opponents[l_idx][w_idx] += 1

        # Initialize strengths as list (faster than dict in hot loop)
        theta = [1.0] * n_models

        # Iterative algorithm with adjacency optimization
        for iteration in range(max_iterations):
            old_theta = theta.copy()
            new_theta = [0.0] * n_models

            for m in range(n_models):
                num = wins[m]
                if num == 0:
                    new_theta[m] = 1.0
                    continue

                # Sum over unique opponents only (optimization #2a)
                theta_m = theta[m]
                denom = 0.0
                for opp, count in opponents[m].items():
                    denom += count / (theta_m + theta[opp])

                new_theta[m] = num / denom if denom > 0 else 1.0

            # Normalize to prevent drift
            total = sum(new_theta)
            if total <= 0:
                theta = [1.0] * n_models
            else:
                theta = [(v / total) * n_models for v in new_theta]

            # Check convergence
            max_change = max(abs(theta[m] - old_theta[m]) for m in range(n_models))
            if max_change < tolerance:
                if logger.isEnabledFor(logging.INFO):
                    logger.info("Bradley-Terry converged in %d iterations", iteration + 1)
                break

        # Build results sorted by strength
        indexed_strengths = [(i, theta[i]) for i in range(n_models)]
        indexed_strengths.sort(key=lambda x: x[1], reverse=True)

        results = []
        for rank, (idx, strength) in enumerate(indexed_strengths, 1):
            results.append(BradleyTerryResult(
                model_id=idx_to_model[idx],
                stage_id=stage_id,
                strength=strength,
                rank=rank,
            ))

        # Deferred logging (optimization #4)
        if logger.isEnabledFor(logging.INFO):
            logger.info(
                "Bradley-Terry ranking for %s: %s",
                stage_id,
                [(r.model_id, f"{r.strength:.3f}") for r in results],
            )

        return results

    def compute_mean_scores(
        self,
        stage_id: str,
        judgments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """Compute mean scores per model per criterion.

        Uses streaming aggregation (sum + count) instead of storing all scores
        in lists (optimization #3a).

        Args:
            stage_id: Stage to analyze
            judgments: Pre-fetched judgments (optional, for batch operations)

        Returns:
            Dict mapping model_id -> {criterion: mean_score}
        """
        if judgments is None:
            judgments = self._get_judgments(stage_id)

        # Streaming aggregation: store sum and count, not all values (optimization #3a)
        totals: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
            lambda: defaultdict(lambda: {"sum": 0.0, "count": 0})
        )

        for j in judgments:
            if j["scores"]:
                model = j["winner_model_id"]
                for criterion, score in j["scores"].items():
                    agg = totals[model][criterion]
                    agg["sum"] += score
                    agg["count"] += 1

        # Compute means
        results = {}
        for model, criteria in totals.items():
            results[model] = {
                criterion: agg["sum"] / agg["count"]
                for criterion, agg in criteria.items()
            }

        return results

    def compute_tag_frequencies(
        self,
        stage_id: str,
        judgments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Dict[str, int]]:
        """Compute tag frequencies per model.

        Args:
            stage_id: Stage to analyze
            judgments: Pre-fetched judgments (optional, for batch operations)

        Returns:
            Dict mapping model_id -> {tag: count}
        """
        if judgments is None:
            judgments = self._get_judgments(stage_id)

        tag_counts: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for j in judgments:
            if j["tags"]:
                model = j["winner_model_id"]
                for tag in j["tags"]:
                    tag_counts[model][tag] += 1

        return dict(tag_counts)

    def generate_report(
        self,
        stage_id: str,
        include_bradley_terry: bool = True,
        include_pairwise: bool = True,
    ) -> Dict:
        """Generate a comprehensive analysis report for a stage.

        Pre-fetches all data once and passes to sub-methods to minimize
        DB calls (optimization #6).

        Args:
            stage_id: Stage to analyze
            include_bradley_terry: Whether to include Bradley-Terry ranking
            include_pairwise: Whether to include pairwise comparisons

        Returns:
            Dict containing all analysis results
        """
        # Pre-fetch all data once (optimization #6)
        stats = self._get_model_stats(stage_id)
        judgments = self._get_judgments(stage_id)
        head_to_head_counts = self._get_head_to_head_counts(stage_id)

        # For Bradley-Terry, we need the raw pairwise data
        pairwise_data = None
        if include_bradley_terry:
            pairwise_data = self.db.get_all_pairwise(stage_id)

        report = {
            "stage_id": stage_id,
            "win_rates": [
                r.to_dict() for r in self.compute_win_rates(stage_id, stats=stats)
            ],
            "mean_scores": self.compute_mean_scores(stage_id, judgments=judgments),
            "tag_frequencies": self.compute_tag_frequencies(stage_id, judgments=judgments),
        }

        if include_pairwise:
            report["pairwise_comparisons"] = [
                r.to_dict()
                for r in self.all_pairwise_comparisons(
                    stage_id, stats=stats, head_to_head_counts=head_to_head_counts
                )
            ]

        if include_bradley_terry:
            report["bradley_terry"] = [
                r.to_dict()
                for r in self.bradley_terry_ranking(
                    stage_id, pairwise_data=pairwise_data
                )
            ]

        return report
