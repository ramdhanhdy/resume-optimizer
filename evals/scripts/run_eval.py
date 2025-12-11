#!/usr/bin/env python
"""CLI script to run evaluations with multiple model candidates.

This script runs REAL LLM agents by default for meaningful evaluation data.
Use --mock flag only for testing the evaluation framework itself.

Usage:
    # Run real evaluation with actual LLM agents
    python -m evals.scripts.run_eval --stage optimizer \
        --models "anthropic/claude-sonnet-4-20250514" "google/gemini-2.0-flash-001" \
        --profile-file data/sample_profile.txt \
        --job-file data/sample_job.txt

    # With GitHub profile enrichment (requires token)
    python -m evals.scripts.run_eval --stage profile \
        --models "anthropic/claude-sonnet-4-20250514" \
        --profile-file data/sample_profile.txt \
        --job-file data/sample_job.txt \
        --github-username octocat \
        --github-token ghp_xxxxxxxxxxxx

    # Test framework only (no API calls)
    python -m evals.scripts.run_eval --stage optimizer --mock \
        --models "model/a" "model/b" \
        --profile-file data/sample_profile.txt \
        --job-file data/sample_job.txt

Requirements:
    - Backend dependencies installed (pip install -e backend/)
    - API keys configured in backend/.env (OPENROUTER_API_KEY, etc.)
    - GitHub token required when using --github-username
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Add project root to path for evals namespace imports
evals_root = Path(__file__).parent.parent
project_root = evals_root.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add backend to path for agent imports
backend_root = project_root / "backend"
backend_src = backend_root / "src"
for p in (backend_root, backend_src):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Load backend/.env for API keys
backend_env = backend_root / ".env"
if backend_env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(backend_env)
    except ImportError:
        pass  # dotenv not installed, assume env vars are set externally

from evals.db.eval_db import EvalDatabase
from evals.framework.runner import EvalRunner
from evals.framework.schemas import CandidateConfig
from evals.framework.config_resume import get_resume_eval_config, CANDIDATE_MODELS


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
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock runner instead of real agents (for testing framework only)",
    )
    parser.add_argument(
        "--github-username",
        type=str,
        help="GitHub username for profile enrichment",
    )
    parser.add_argument(
        "--github-token",
        type=str,
        help="GitHub personal access token (required with --github-username)",
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


def create_real_runner(stage_id: str):
    """Create a runner function that calls actual backend agents.
    
    Args:
        stage_id: The pipeline stage to run (profile, job_analyzer, optimizer, qa, polish)
        
    Returns:
        A runner function compatible with EvalRunner.run_stage_eval_sync
    """
    def run_agent(cfg: CandidateConfig, context: Dict[str, Any]) -> str:
        """Run the appropriate agent for the given stage."""
        # Change to backend directory so prompt files are found
        original_cwd = os.getcwd()
        os.chdir(backend_root)
        
        try:
            from src.api.client_factory import create_client
            client = create_client()
            
            if stage_id == "profile":
                from src.agents.profile_agent import ProfileAgent
                
                # Fetch GitHub repos if username and token provided
                profile_repos = context.get("profile_repos")
                github_username = context.get("github_username")
                github_token = context.get("github_token")
                
                if github_username and github_token and not profile_repos:
                    try:
                        from src.agents.github_projects_agent import fetch_github_repos
                        profile_repos = fetch_github_repos(github_username, github_token, max_repos=20)
                    except Exception as e:
                        # Log but continue without repos
                        print(f"⚠️ Failed to fetch GitHub repos: {e}")
                        profile_repos = None
                
                agent = ProfileAgent(client=client)
                result = ""
                gen = agent.index_profile(
                    model=cfg.model_id,
                    profile_text=context.get("profile", ""),
                    profile_repos=profile_repos,
                    temperature=cfg.temperature,
                )
                try:
                    while True:
                        chunk = next(gen)
                        result += chunk
                except StopIteration:
                    pass
                return result
                
            elif stage_id == "job_analyzer":
                from src.agents import JobAnalyzerAgent
                agent = JobAnalyzerAgent(client=client)
                result = ""
                gen = agent.analyze_job(
                    job_posting=context.get("job_posting", ""),
                    model=cfg.model_id,
                    temperature=cfg.temperature,
                )
                try:
                    while True:
                        chunk = next(gen)
                        result += chunk
                except StopIteration:
                    pass
                return result
                
            elif stage_id == "optimizer":
                from src.agents import ResumeOptimizerAgent
                agent = ResumeOptimizerAgent(client=client)
                result = ""
                gen = agent.optimize_resume(
                    resume_text=context.get("profile", ""),
                    job_analysis=context.get("job_analysis", context.get("job_posting", "")),
                    profile_index=context.get("profile_index"),
                    model=cfg.model_id,
                    temperature=cfg.temperature,
                )
                try:
                    while True:
                        chunk = next(gen)
                        result += chunk
                except StopIteration:
                    pass
                return result
                
            elif stage_id == "qa":
                from src.agents import ValidatorAgent
                agent = ValidatorAgent(client=client)
                result = ""
                gen = agent.validate_resume(
                    optimized_resume=context.get("optimized_resume", context.get("profile", "")),
                    job_posting=context.get("job_posting", ""),
                    job_analysis=context.get("job_analysis", ""),
                    profile_index=context.get("profile_index"),
                    model=cfg.model_id,
                    temperature=cfg.temperature,
                )
                try:
                    while True:
                        chunk = next(gen)
                        result += chunk
                except StopIteration:
                    pass
                return result
                
            elif stage_id == "polish":
                from src.agents import PolishAgent
                agent = PolishAgent(client=client, output_format="docx")
                result = ""
                gen = agent.polish_resume(
                    optimized_resume=context.get("optimized_resume", context.get("profile", "")),
                    validation_report=context.get("validation_report", ""),
                    model=cfg.model_id,
                    temperature=cfg.temperature,
                )
                try:
                    while True:
                        chunk = next(gen)
                        result += chunk
                except StopIteration:
                    pass
                return result
                
            else:
                return f"[Stage '{stage_id}' not implemented]"
                
        except ImportError as e:
            return f"[ERROR] Backend import failed: {e}\n\nEnsure backend dependencies are installed and API keys are set in .env"
        except Exception as e:
            return f"[ERROR] {type(e).__name__}: {e}"
        finally:
            os.chdir(original_cwd)
    
    return run_agent


def create_mock_runner(stage_id: str):
    """Create a mock runner function for testing without actual API calls.
    
    DEPRECATED: Use create_real_runner() for production evaluations.
    """
    def mock_run(cfg: CandidateConfig, context: dict) -> str:
        model_name = cfg.model_id.split("/")[-1]
        return f"""[MOCK OUTPUT - NOT REAL LLM RESPONSE]

This is a simulated response for stage: {stage_id}
Model: {cfg.model_id}
Temperature: {cfg.temperature}

Profile summary: {context.get('profile', 'N/A')[:100]}...
Job summary: {context.get('job_posting', 'N/A')[:100]}...

Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}

WARNING: This output was generated by the mock runner.
To get real LLM outputs, run without --mock flag.
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

    # Validate GitHub args
    if args.github_username and not args.github_token:
        print("⚠️  WARNING: --github-username provided without --github-token")
        print("   GitHub integration will fail. Provide token or remove username.\n")

    # Create scenario
    scenario = runner.create_scenario(
        user_profile=profile,
        job_posting=job_posting,
        metadata={
            "source": "cli",
            "stage": args.stage,
            "models": args.models,
            "github_username": args.github_username,
            "has_github_token": bool(args.github_token),
        },
    )
    print(f"Created scenario: {scenario.scenario_id}")

    # Build context
    context = {
        "profile": profile,
        "job_posting": job_posting,
    }
    
    if args.github_username:
        context["github_username"] = args.github_username
    if args.github_token:
        context["github_token"] = args.github_token

    # Run evaluation with real agents (or mock if --mock flag is set)
    print(f"\nRunning {len(candidates)} candidates...")
    
    if args.mock:
        print("⚠️  WARNING: Using mock runner - outputs are NOT from real LLMs!")
        print("   Remove --mock flag for production evaluations.\n")
        agent_runner = create_mock_runner(args.stage)
    else:
        print("🤖 Using real LLM agents...")
        agent_runner = create_real_runner(args.stage)

    stage_eval = runner.run_stage_eval_sync(
        scenario_id=scenario.scenario_id,
        stage_id=args.stage,
        context=context,
        candidates=candidates,
        runner_fn=agent_runner,
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
