"""Profile Agent Arena evaluation harness.

- Compares two ProfileAgent variants (models from model_registry) on the same evidence.
- Uses DeepEval Arena (if installed) with grounding-focused evaluation_steps.
- Writes JSON results (no database writes) under evals/profile_agent_arena/results/.

Usage (from backend/):

    python -m evals.profile_agent_arena.run_profile_agent_arena \
        --db-path ./data/applications.db \
        --models "openrouter::qwen/qwen3-max" "openrouter::anthropic/claude-sonnet-4.5" \
        --limit 5 \
        --judge-model "gpt-5.1"

Notes:
- Contestant models must exist in src.api.model_registry.MODEL_REGISTRY.
- Requires API keys for the chosen providers (same as runtime). 
- DeepEval must be installed separately: `pip install deepeval`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Core imports (do not modify core backend code)
from src.agents.profile_agent import ProfileAgent
from src.api.client_factory import create_client
from src.api.model_registry import MODEL_REGISTRY

RESULTS_DIR = Path(__file__).resolve().parent / "results"
REQUIRED_KEYS = {
    "summary",
    "skills_taxonomy",
    "roles",
    "projects",
    "claims_ledger",
    "snippet_pack",
    "notes_for_editors",
}


def _now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ProfileAgent Arena evaluation harness")
    parser.add_argument(
        "--db-path",
        default="./data/applications.db",
        help="Path to SQLite DB with profiles table",
    )
    parser.add_argument(
        "--models",
        nargs=2,
        metavar=("MODEL_A", "MODEL_B"),
        required=True,
        help="Two models (contestants) from MODEL_REGISTRY",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of profiles to evaluate",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset into profiles table (for sampling different slices)",
    )
    parser.add_argument(
        "--judge-model",
        default="gpt-5.1",
        help="Model used by DeepEval Arena judge (not constrained by model_registry)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Temperature to use for both contestants",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=3500,
        help="Max tokens to request from ProfileAgent",
    )
    return parser.parse_args()


def validate_models(models: List[str]) -> None:
    missing = [m for m in models if m.lower() not in MODEL_REGISTRY]
    if missing:
        raise SystemExit(f"Models not in MODEL_REGISTRY: {missing}")


def load_profiles(db_path: str, limit: int, offset: int) -> List[Dict[str, Any]]:
    if not Path(db_path).exists():
        raise SystemExit(f"DB not found at {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, sources, profile_text
        FROM profiles
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        try:
            sources = json.loads(r["sources"] or "[]")
        except Exception:
            sources = []
        result.append(
            {
                "id": r["id"],
                "sources": sources,
                "profile_text": r["profile_text"] or "",
            }
        )
    return result


def run_profile_agent(
    model: str,
    profile_text: str,
    *,
    temperature: float,
    max_tokens: int,
    profile_repos: Optional[list] = None,
) -> str:
    client = create_client()
    agent = ProfileAgent(client=client)
    chunks = []
    stream = agent.index_profile(
        model=model,
        profile_text=profile_text,
        profile_repos=profile_repos,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    try:
        for chunk in stream:
            chunks.append(chunk)
    except StopIteration:
        pass
    return "".join(chunks)


def precheck_output(output_text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "valid_json": True,
        "missing_keys": [],
        "error": None,
        "length": len(output_text or ""),
    }
    try:
        obj = json.loads(output_text)
    except Exception as e:  # invalid JSON
        result["valid_json"] = False
        result["error"] = str(e)
        return result

    missing = [k for k in REQUIRED_KEYS if k not in obj]
    if missing:
        result["missing_keys"] = missing
    return result


def build_arena_test_case(evidence: str, output_a: str, output_b: str):
    try:
        from deepeval.test_case import ArenaTestCase, Contestant, LLMTestCase
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "deepeval is required for Arena evaluation. Install with `pip install deepeval`"
        ) from e

    contestant_a = Contestant(
        name="Contestant A",
        test_case=LLMTestCase(
            input="Build profile index for downstream resume optimization.",
            actual_output=output_a,
            context=[evidence],
        ),
    )
    contestant_b = Contestant(
        name="Contestant B",
        test_case=LLMTestCase(
            input="Build profile index for downstream resume optimization.",
            actual_output=output_b,
            context=[evidence],
        ),
    )
    return ArenaTestCase(contestants=[contestant_a, contestant_b])


def run_arena_judge(test_cases, judge_model: str) -> List[Dict[str, Any]]:
    try:
        from deepeval.metrics import ArenaGEval
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "deepeval is required for Arena evaluation. Install with `pip install deepeval`"
        ) from e

    metric = ArenaGEval(
        evaluation_steps=[
            "Validate JSON and required schema keys (summary, skills_taxonomy, roles, projects, claims_ledger, snippet_pack, notes_for_editors).",
            "Reject any fabricated employers/titles/dates/metrics/projects not in evidence.",
            "Check grounding quality: claims_ledger evidence excerpts should plausibly appear in evidence and match claims; confidence should be conservative.",
            "Check usefulness: skills_taxonomy and projects should be relevant; snippet_pack bullets should be resume-ready and conservative.",
            "Choose the better contestant; tie if equivalent.",
        ],
        model=judge_model,
    )

    # metric.compare returns ArenaResult(s); keep it simple and capture winner + reasoning
    results = []
    for case in test_cases:
        try:
            arena_result = metric.compare(test_cases=[case])[0]
            results.append(
                {
                    "winner": arena_result.winner,
                    "reason": getattr(arena_result, "reason", ""),
                }
            )
        except Exception as e:  # pragma: no cover
            results.append({"winner": "error", "reason": str(e)})
    return results


def main():
    args = parse_args()
    validate_models(args.models)

    profiles = load_profiles(args.db_path, args.limit, args.offset)
    if not profiles:
        raise SystemExit("No profiles found to evaluate.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = f"profile-arena-{uuid.uuid4()}"

    cases_payload = []
    test_cases = []

    for prof in profiles:
        evidence = prof["profile_text"]
        output_a = run_profile_agent(
            args.models[0], evidence, temperature=args.temperature, max_tokens=args.max_tokens
        )
        output_b = run_profile_agent(
            args.models[1], evidence, temperature=args.temperature, max_tokens=args.max_tokens
        )

        pre_a = precheck_output(output_a)
        pre_b = precheck_output(output_b)

        # Decide early if JSON invalid and short-circuit arena when possible
        winner = None
        reason = None
        if not pre_a["valid_json"] and pre_b["valid_json"]:
            winner, reason = "Contestant B", "A invalid JSON"
        elif not pre_b["valid_json"] and pre_a["valid_json"]:
            winner, reason = "Contestant A", "B invalid JSON"
        elif not pre_a["valid_json"] and not pre_b["valid_json"]:
            winner, reason = "Tie", "Both invalid JSON"
        else:
            tc = build_arena_test_case(evidence, output_a, output_b)
            test_cases.append(tc)
            # Winner decided later via Arena judge

        cases_payload.append(
            {
                "case_id": prof["id"],
                "sources": prof["sources"],
                "evidence_chars": len(evidence),
                "outputs": {
                    "contestant_a": {"length": len(output_a), **pre_a},
                    "contestant_b": {"length": len(output_b), **pre_b},
                },
                "precheck_winner": winner,
                "precheck_reason": reason,
            }
        )

    arena_results = []
    if test_cases:
        arena_results = run_arena_judge(test_cases, args.judge_model)

    # Merge arena results back into payload in order of judged cases
    judged_idx = 0
    for case in cases_payload:
        if case["precheck_winner"] is None:
            ar = arena_results[judged_idx]
            case["arena_winner"] = ar.get("winner")
            case["arena_reason"] = ar.get("reason")
            judged_idx += 1
        else:
            case["arena_winner"] = None
            case["arena_reason"] = None

        # Final winner decision
        if case["precheck_winner"]:
            case["winner"] = case["precheck_winner"]
            case["winner_reason"] = case["precheck_reason"]
        else:
            case["winner"] = case.get("arena_winner")
            case["winner_reason"] = case.get("arena_reason")

    # Aggregate stats
    agg = {"Contestant A": 0, "Contestant B": 0, "Tie": 0, "error": 0}
    for case in cases_payload:
        w = case.get("winner")
        if w in agg:
            agg[w] += 1
        else:
            agg["error"] += 1

    result = {
        "run_id": run_id,
        "timestamp": _now_iso(),
        "db_path": args.db_path,
        "models": {"contestant_a": args.models[0], "contestant_b": args.models[1]},
        "judge_model": args.judge_model,
        "cases": cases_payload,
        "aggregate": agg,
    }

    out_path = RESULTS_DIR / f"{run_id}.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"✅ Arena evaluation complete. Results saved to {out_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
