"""Streamlit UI for ProfileAgent Arena evaluation.

Features:
- Select contestant models from model_registry.
- Choose judge model (default gpt-5.1).
- Data sources:
  - Fresh fetch: LinkedIn URL (via Exa) and/or GitHub username (via PyGithub), optional manual text.
  - DB sample: sample rows from profiles table.
- Runs ProfileAgent for both contestants, applies deterministic prechecks, then ArenaGEval judge.
- Saves JSON results under results/ and displays summary tables in UI.

Usage (from backend/):
    streamlit run evals/profile_agent_arena/streamlit_app.py

Note: Requires `deepeval`, `streamlit`, and provider API keys (EXA_API_KEY, GitHub token optional).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Load .env from backend root (two levels up from this file)
_env_path = Path(__file__).resolve().parents[2] / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

import streamlit as st

from src.api.model_registry import MODEL_REGISTRY
from src.api.exa_client import fetch_public_page_text, ExaContentError
from src.agents.github_projects_agent import fetch_github_repos

from evals.profile_agent_arena.run_profile_agent_arena import (
    RESULTS_DIR,
    build_arena_test_case,
    load_profiles,
    precheck_output,
    run_arena_judge,
    run_profile_agent,
)

# -------- Helpers --------


def _now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _list_models() -> List[str]:
    return sorted(MODEL_REGISTRY.keys())


def _combine_evidence(profile_text: str, profile_repos: Optional[list]) -> str:
    if not profile_repos:
        return profile_text or ""
    try:
        repos_str = json.dumps(profile_repos[:8], ensure_ascii=False, indent=2)
    except Exception:
        repos_str = ""
    return (profile_text or "") + "\n\n<repos_json>\n" + repos_str + "\n</repos_json>"


def _save_result(payload: Dict[str, Any]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{payload['run_id']}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


# -------- UI Sections --------

def sidebar_controls():
    st.sidebar.header("Contestants")
    models = _list_models()
    model_a = st.sidebar.selectbox("Model A", models, index=0)
    model_b = st.sidebar.selectbox("Model B", models, index=1 if len(models) > 1 else 0)

    st.sidebar.header("Judge")
    judge_model = st.sidebar.text_input("Judge model", value="gpt-5.1")
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.1, 0.05)
    max_tokens = st.sidebar.number_input("Max tokens", min_value=512, max_value=8000, value=3500, step=100)
    return model_a, model_b, judge_model, temperature, max_tokens


def data_source_controls():
    st.header("Data Source")
    source = st.radio("Choose evidence source", ["Fresh fetch", "DB sample"], index=0)
    fresh_inputs = {}
    db_inputs = {}

    if source == "Fresh fetch":
        st.subheader("Fresh fetch (LinkedIn / GitHub / manual text)")
        linkedin_url = st.text_input("LinkedIn or public profile URL (optional)")
        github_username = st.text_input("GitHub username (optional)")
        github_token = st.text_input("GitHub token (optional, uses GITHUB_TOKEN env if blank)", type="password")
        manual_text = st.text_area("Manual evidence text (optional)", height=150)
        fresh_inputs = {
            "linkedin_url": linkedin_url.strip(),
            "github_username": github_username.strip(),
            "github_token": github_token.strip(),
            "manual_text": manual_text,
        }
    else:
        st.subheader("DB sample (profiles table)")
        db_path = st.text_input("DB path", value="./data/applications.db")
        limit = st.number_input("Limit", min_value=1, max_value=50, value=5, step=1)
        offset = st.number_input("Offset", min_value=0, max_value=500, value=0, step=1)
        db_inputs = {"db_path": db_path.strip(), "limit": int(limit), "offset": int(offset)}

    return source, fresh_inputs, db_inputs


def fetch_fresh_evidence(linkedin_url: str, github_username: str, manual_text: str, github_token: str = "") -> Dict[str, Any]:
    profile_text_parts = []
    repos = None

    if linkedin_url:
        try:
            text = fetch_public_page_text(linkedin_url)
            profile_text_parts.append(text)
        except (ExaContentError, RuntimeError, ValueError) as e:
            raise RuntimeError(f"LinkedIn/public fetch failed: {e}") from e

    if github_username:
        try:
            token = github_token or os.getenv("GITHUB_TOKEN")
            repos = fetch_github_repos(github_username, token=token, max_repos=12)
        except Exception as e:
            raise RuntimeError(f"GitHub fetch failed: {e}") from e

    if manual_text:
        profile_text_parts.append(manual_text)

    combined = "\n\n".join([p for p in profile_text_parts if p])
    if not combined and not repos:
        raise RuntimeError("No evidence provided. Add a URL, GitHub username, or manual text.")

    return {"profile_text": combined, "profile_repos": repos}


def build_cases_from_db(db_path: str, limit: int, offset: int) -> List[Dict[str, Any]]:
    rows = load_profiles(db_path, limit, offset)
    cases = []
    for r in rows:
        cases.append(
            {
                "case_id": r["id"],
                "sources": r["sources"],
                "profile_text": r["profile_text"],
                "profile_repos": None,
            }
        )
    return cases


def build_cases_fresh(fresh: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "case_id": f"fresh-{uuid.uuid4().hex[:8]}",
            "sources": [],
            "profile_text": fresh["profile_text"],
            "profile_repos": fresh.get("profile_repos"),
        }
    ]


def run_cases(cases: List[Dict[str, Any]], model_a: str, model_b: str, judge_model: str, temperature: float, max_tokens: int):
    cases_payload = []
    test_cases = []

    for prof in cases:
        evidence_str = _combine_evidence(prof["profile_text"], prof.get("profile_repos"))

        output_a = run_profile_agent(
            model_a,
            prof["profile_text"],
            temperature=temperature,
            max_tokens=max_tokens,
            profile_repos=prof.get("profile_repos"),
        )
        output_b = run_profile_agent(
            model_b,
            prof["profile_text"],
            temperature=temperature,
            max_tokens=max_tokens,
            profile_repos=prof.get("profile_repos"),
        )

        pre_a = precheck_output(output_a)
        pre_b = precheck_output(output_b)

        winner = None
        reason = None
        if not pre_a["valid_json"] and pre_b["valid_json"]:
            winner, reason = "Contestant B", "A invalid JSON"
        elif not pre_b["valid_json"] and pre_a["valid_json"]:
            winner, reason = "Contestant A", "B invalid JSON"
        elif not pre_a["valid_json"] and not pre_b["valid_json"]:
            winner, reason = "Tie", "Both invalid JSON"
        else:
            tc = build_arena_test_case(evidence_str, output_a, output_b)
            test_cases.append(tc)

        cases_payload.append(
            {
                "case_id": prof["case_id"],
                "sources": prof.get("sources", []),
                "evidence_chars": len(evidence_str),
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
        arena_results = run_arena_judge(test_cases, judge_model)

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

        case["winner"] = case["precheck_winner"] or case.get("arena_winner")
        case["winner_reason"] = case["precheck_reason"] or case.get("arena_reason")

    agg = {"Contestant A": 0, "Contestant B": 0, "Tie": 0, "error": 0}
    for case in cases_payload:
        w = case.get("winner")
        if w in agg:
            agg[w] += 1
        else:
            agg["error"] += 1

    return cases_payload, agg


# -------- Main UI --------

def main():
    st.title("ProfileAgent Arena Runner")
    st.caption("Select models, pick data source, fetch evidence, and run an Arena evaluation.")

    model_a, model_b, judge_model, temperature, max_tokens = sidebar_controls()
    source, fresh_inputs, db_inputs = data_source_controls()

    if st.button("Run evaluation", type="primary"):
        try:
            if source == "Fresh fetch":
                fresh = fetch_fresh_evidence(
                    fresh_inputs.get("linkedin_url", ""),
                    fresh_inputs.get("github_username", ""),
                    fresh_inputs.get("manual_text", ""),
                    fresh_inputs.get("github_token", ""),
                )
                cases = build_cases_fresh(fresh)
            else:
                cases = build_cases_from_db(**db_inputs)
                if not cases:
                    st.error("No cases found from DB.")
                    return

            with st.spinner("Running ProfileAgent and Arena judge..."):
                cases_payload, agg = run_cases(
                    cases, model_a, model_b, judge_model, temperature, max_tokens
                )

            run_id = f"profile-arena-{uuid.uuid4()}"
            payload = {
                "run_id": run_id,
                "timestamp": _now_iso(),
                "models": {"contestant_a": model_a, "contestant_b": model_b},
                "judge_model": judge_model,
                "cases": cases_payload,
                "aggregate": agg,
                "source": source,
            }
            out_path = _save_result(payload)

            st.success(f"Run complete. Saved to {out_path}")
            st.subheader("Aggregate")
            st.json(agg)

            st.subheader("Cases")
            st.dataframe(
                [
                    {
                        "case_id": c["case_id"],
                        "winner": c.get("winner"),
                        "reason": c.get("winner_reason"),
                        "precheck_winner": c.get("precheck_winner"),
                        "arena_winner": c.get("arena_winner"),
                        "evidence_chars": c.get("evidence_chars"),
                        "a_valid": c["outputs"]["contestant_a"]["valid_json"],
                        "b_valid": c["outputs"]["contestant_b"]["valid_json"],
                    }
                    for c in cases_payload
                ]
            )

            with st.expander("Full JSON payload"):
                st.json(payload)

        except SystemExit as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Run failed: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
