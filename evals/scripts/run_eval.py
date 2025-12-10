#!/usr/bin/env python
"""CLI script to run evaluations with multiple model candidates.

Usage:
    python -m evals.scripts.run_eval --stage optimizer \
        --models "anthropic/claude-sonnet-4-20250514" "google/gemini-2.0-flash-001" \
        --profile-file data/sample_profile.txt \
        --job-file data/sample_job.txt
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

# Add evals root to path
evals_root = Path(__file__).parent.parent
sys.path.insert(0, str(evals_root))

from db.eval_db import EvalDatabase
from framework.runner import EvalRunner
from framework.schemas import CandidateConfig
from framework.config_resume import get_resume_eval_config, CANDIDATE_MODELS


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run evaluation with multiple model candidates"
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="optimizer",
        choices=["profile", "job_analyzer", "optimizer", "qa", "polish"],
        help="Pipeline stage to evaluate",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        help="Model IDs to evaluate (space-separated)",
    )
    parser.add_argument(
        "--profile-file",
        type=str,
        help="Path to file containing user profile/resume",
    )
    parser.add_argument(
        "--job-file",
        type=str,
        help="Path to file containing job posting",
    )
    parser.add_argument(
        "--profile",
        type=str,
        help="User profile text (alternative to --profile-file)",
    )
    parser.add_argument(
        "--job",
        type=str,
        help="Job posting text (alternative to --job-file)",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to evaluation database",
    )
    parser.add_argument(
        "--no-randomize",
        action="store_true",
        help="Don't randomize candidate order",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be run without executing",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models and exit",
    )
    return parser.parse_args()


def list_available_models():
    """Print available models."""
    print("\nAvailable models:")
    print("-" * 60)
    for model in CANDIDATE_MODELS:
        print(f"  {model.model_id}")
        print(f"    Display: {model.display_name}")
        print(f"    Provider: {model.provider}")
        print()


def load_text_file(path: str) -> str:
    """Load text from file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def create_mock_runner(stage_id: str):
    """Create a mock runner function for testing without actual API calls."""
    def mock_run(cfg: CandidateConfig, context: dict) -> str:
        # Simulate different outputs based on model
        model_name = cfg.model_id.split("/")[-1]
        return f"""[Mock output from {model_name}]

This is a simulated response for stage: {stage_id}

Profile summary: {context.get('profile', 'N/A')[:100]}...
Job summary: {context.get('job_posting', 'N/A')[:100]}...

Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}
Model: {cfg.model_id}
Temperature: {cfg.temperature}
"""
    return mock_run


def main():
    args = parse_args()

    if args.list_models:
        list_available_models()
        return

    # Get configuration
    config = get_resume_eval_config()
    db_path = args.db_path or config.db_path

    # Validate inputs
    if not args.models:
        print("Error: --models is required")
        print("Use --list-models to see available models")
        sys.exit(1)

    # Load profile
    profile = None
    if args.profile_file:
        profile = load_text_file(args.profile_file)
    elif args.profile:
        profile = args.profile
    else:
        print("Error: --profile-file or --profile is required")
        sys.exit(1)

    # Load job posting
    job_posting = None
    if args.job_file:
        job_posting = load_text_file(args.job_file)
    elif args.job:
        job_posting = args.job
    else:
        print("Error: --job-file or --job is required")
        sys.exit(1)

    # Build candidate configs
    candidates = [
        CandidateConfig(model_id=model_id)
        for model_id in args.models
    ]

    print(f"\nEvaluation Configuration:")
    print(f"  Stage: {args.stage}")
    print(f"  Models: {len(candidates)}")
    for cfg in candidates:
        print(f"    - {cfg.model_id}")
    print(f"  Profile length: {len(profile)} chars")
    print(f"  Job posting length: {len(job_posting)} chars")
    print(f"  Database: {db_path}")
    print(f"  Randomize: {not args.no_randomize}")
    print()

    if args.dry_run:
        print("Dry run - no evaluation executed")
        return

    # Initialize database and runner
    db = EvalDatabase(db_path)
    runner = EvalRunner(db)

    # Create scenario
    scenario = runner.create_scenario(
        user_profile=profile,
        job_posting=job_posting,
        metadata={
            "source": "cli",
            "stage": args.stage,
            "models": args.models,
        },
    )
    print(f"Created scenario: {scenario.scenario_id}")

    # Build context
    context = {
        "profile": profile,
        "job_posting": job_posting,
    }

    # Run evaluation with mock runner (replace with real runner for production)
    print(f"\nRunning {len(candidates)} candidates...")
    mock_runner = create_mock_runner(args.stage)

    stage_eval = runner.run_stage_eval_sync(
        scenario_id=scenario.scenario_id,
        stage_id=args.stage,
        context=context,
        candidates=candidates,
        runner_fn=mock_runner,
        randomize=not args.no_randomize,
    )

    print(f"\nCompleted stage evaluation (ID: {stage_eval.id})")
    print(f"\nCandidate outputs:")
    for candidate in stage_eval.candidates:
        print(f"\n--- Option {candidate.candidate_label} ---")
        print(f"Latency: {candidate.latency_ms}ms")
        print(f"Output preview: {candidate.output_text[:200]}...")

    print(f"\n✓ Evaluation ready for judgment")
    print(f"  Run the judge UI: streamlit run evals/ui/app.py")


if __name__ == "__main__":
    main()
