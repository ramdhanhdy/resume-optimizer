#!/usr/bin/env python
"""CLI script to analyze evaluation results.

Usage:
    python -m evals.scripts.analyze_results --stage optimizer
    python -m evals.scripts.analyze_results --stage optimizer --format json
    python -m evals.scripts.analyze_results --stage optimizer --export results.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path for evals namespace imports
evals_root = Path(__file__).parent.parent
project_root = evals_root.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from evals.db.eval_db import EvalDatabase
from evals.framework.analyzer import EvalAnalyzer
from evals.framework.config_resume import get_resume_eval_config, RESUME_STAGES


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze evaluation results"
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="optimizer",
        choices=list(RESUME_STAGES.keys()),
        help="Pipeline stage to analyze",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to evaluation database",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export results to file",
    )
    parser.add_argument(
        "--pairwise",
        nargs=2,
        metavar=("MODEL_A", "MODEL_B"),
        help="Show pairwise comparison between two models",
    )
    return parser.parse_args()


def print_text_report(analyzer: EvalAnalyzer, stage_id: str):
    """Print human-readable analysis report."""
    stage_config = RESUME_STAGES[stage_id]
    
    print(f"\n{'=' * 60}")
    print(f"Analysis Report: {stage_config.display_name}")
    print(f"{'=' * 60}")

    # Win rates
    print(f"\n## Win Rates")
    print("-" * 40)
    win_rates = analyzer.compute_win_rates(stage_id)
    
    if not win_rates:
        print("No evaluation data available.")
        return
    
    for result in win_rates:
        model_short = result.model_id.split("/")[-1]
        bar = "█" * int(result.win_rate * 20)
        print(f"  {model_short:30} {result.win_rate:6.1%} {bar}")
        print(f"    ({result.wins} wins / {result.appearances} appearances)")

    # Bradley-Terry ranking
    print(f"\n## Bradley-Terry Ranking")
    print("-" * 40)
    bt_results = analyzer.bradley_terry_ranking(stage_id)
    
    if bt_results:
        for result in bt_results:
            model_short = result.model_id.split("/")[-1]
            print(f"  #{result.rank} {model_short:30} (strength: {result.strength:.3f})")
    else:
        print("  Insufficient data for ranking.")

    # Pairwise comparisons
    print(f"\n## Pairwise Comparisons")
    print("-" * 40)
    pairwise = analyzer.all_pairwise_comparisons(stage_id)
    
    if pairwise:
        for result in pairwise:
            a_short = result.model_a.split("/")[-1][:15]
            b_short = result.model_b.split("/")[-1][:15]
            sig = "*" if result.significant else ""
            print(
                f"  {a_short} vs {b_short}: "
                f"P(A>B)={result.p_a_preferred:.2f} "
                f"CI=[{result.ci_low:.2f}, {result.ci_high:.2f}] "
                f"N={result.total} {sig}"
            )
        print("\n  * = statistically significant (95% CI excludes 0.5)")
    else:
        print("  No pairwise data available.")

    # Mean scores
    print(f"\n## Mean Scores by Criterion")
    print("-" * 40)
    mean_scores = analyzer.compute_mean_scores(stage_id)
    
    if mean_scores:
        for model, criteria in mean_scores.items():
            model_short = model.split("/")[-1]
            print(f"  {model_short}:")
            for criterion, score in criteria.items():
                print(f"    {criterion}: {score:.2f}/5")
    else:
        print("  No score data available.")

    # Tag frequencies
    print(f"\n## Tag Frequencies")
    print("-" * 40)
    tag_freqs = analyzer.compute_tag_frequencies(stage_id)
    
    if tag_freqs:
        for model, tags in tag_freqs.items():
            model_short = model.split("/")[-1]
            print(f"  {model_short}:")
            for tag, count in sorted(tags.items(), key=lambda x: -x[1]):
                print(f"    {tag}: {count}")
    else:
        print("  No tag data available.")

    print(f"\n{'=' * 60}\n")


def print_pairwise_comparison(
    analyzer: EvalAnalyzer,
    stage_id: str,
    model_a: str,
    model_b: str,
):
    """Print detailed pairwise comparison."""
    result = analyzer.pairwise_preference(stage_id, model_a, model_b)
    
    a_short = model_a.split("/")[-1]
    b_short = model_b.split("/")[-1]
    
    print(f"\n{'=' * 60}")
    print(f"Pairwise Comparison: {a_short} vs {b_short}")
    print(f"{'=' * 60}")
    
    print(f"\n  Total comparisons: {result.total}")
    print(f"  {a_short} wins: {result.a_wins}")
    print(f"  {b_short} wins: {result.b_wins}")
    print(f"\n  P({a_short} > {b_short}): {result.p_a_preferred:.3f}")
    print(f"  95% CI: [{result.ci_low:.3f}, {result.ci_high:.3f}]")
    print(f"  p-value: {result.p_value:.4f}")
    
    if result.significant:
        if result.p_a_preferred > 0.5:
            print(f"\n  ✓ {a_short} is significantly preferred over {b_short}")
        else:
            print(f"\n  ✓ {b_short} is significantly preferred over {a_short}")
    else:
        print(f"\n  ○ No significant preference detected")
    
    print(f"\n{'=' * 60}\n")


def main():
    args = parse_args()

    # Get configuration
    config = get_resume_eval_config()
    db_path = args.db_path or config.db_path

    # Check database exists
    if not Path(db_path).exists():
        print(f"Error: Database not found at {db_path}")
        print("Run some evaluations first with: python -m evals.scripts.run_eval")
        sys.exit(1)

    # Initialize
    db = EvalDatabase(db_path)
    analyzer = EvalAnalyzer(db)

    # Handle pairwise comparison
    if args.pairwise:
        print_pairwise_comparison(
            analyzer,
            args.stage,
            args.pairwise[0],
            args.pairwise[1],
        )
        return

    # Generate report
    if args.format == "json":
        report = analyzer.generate_report(args.stage)
        output = json.dumps(report, indent=2)
        
        if args.export:
            with open(args.export, "w") as f:
                f.write(output)
            print(f"Exported to {args.export}")
        else:
            print(output)
    else:
        print_text_report(analyzer, args.stage)
        
        if args.export:
            report = analyzer.generate_report(args.stage)
            with open(args.export, "w") as f:
                json.dump(report, f, indent=2)
            print(f"Exported to {args.export}")


if __name__ == "__main__":
    main()
