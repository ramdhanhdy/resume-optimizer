"""Streamlit app for evaluation UI.

Run with: streamlit run evals/ui/app.py (from project root)
Or: cd evals && streamlit run ui/app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path for evals namespace imports
evals_root = Path(__file__).parent.parent
project_root = evals_root.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add backend/src to path for importing agents and model registry
backend_root = project_root / "backend"
backend_src = backend_root / "src"
sys.path.insert(0, str(backend_root))
sys.path.insert(0, str(backend_src))

from evals.db.eval_db import EvalDatabase
from evals.framework.collector import JudgmentCollector
from evals.framework.config_resume import get_resume_eval_config, RESUME_STAGES
from evals.ui.judge_ui import (
    render_judge_ui,
    render_results_dashboard,
    render_pending_queue,
)
from evals.ui.new_eval import render_new_eval_page


def main():
    st.set_page_config(
        page_title="Resume Optimizer Eval",
        page_icon="📊",
        layout="wide",
    )

    # Initialize database
    config = get_resume_eval_config()
    db = EvalDatabase(config.db_path)
    collector = JudgmentCollector(db)

    # Sidebar navigation
    st.sidebar.title("Evaluation Suite")

    # Evaluator ID
    evaluator_id = st.sidebar.text_input(
        "Evaluator ID",
        value="developer",
        help="Your identifier for tracking judgments",
    )

    page = st.sidebar.radio(
        "Navigation",
        options=["New Evaluation", "Pending Queue", "Results Dashboard", "Browse Scenarios"],
    )

    st.sidebar.divider()

    # Stage filter for results
    if page == "Results Dashboard":
        stage_id = st.sidebar.selectbox(
            "Stage",
            options=list(RESUME_STAGES.keys()),
            format_func=lambda x: RESUME_STAGES[x].display_name,
        )

    st.sidebar.divider()

    # Stats
    st.sidebar.subheader("Quick Stats")
    pending_count = len(db.get_pending_stage_runs(limit=100))
    st.sidebar.metric("Pending", pending_count)

    # Main content
    if page == "New Evaluation":
        render_new_eval_page(db, evaluator_id)

    elif page == "Pending Queue":
        render_pending_queue(db, collector, evaluator_id)

    elif page == "Results Dashboard":
        render_results_dashboard(db, stage_id)

    elif page == "Browse Scenarios":
        render_scenario_browser(db)


def render_scenario_browser(db: EvalDatabase):
    """Browse and inspect scenarios."""
    st.header("Browse Scenarios")

    scenarios = db.list_scenarios(limit=50)

    if not scenarios:
        st.info("No scenarios recorded yet.")
        return

    # Scenario list
    for scenario in scenarios:
        with st.expander(
            f"{scenario.scenario_id} - {scenario.created_at.strftime('%Y-%m-%d %H:%M')}"
        ):
            st.subheader("Job Posting")
            st.text(scenario.job_posting[:500] + "..." if len(scenario.job_posting) > 500 else scenario.job_posting)

            st.subheader("Profile")
            st.text(scenario.user_profile[:500] + "..." if len(scenario.user_profile) > 500 else scenario.user_profile)

            # Stage runs for this scenario
            stage_runs = db.get_stage_runs_for_scenario(scenario.scenario_id)
            if stage_runs:
                st.subheader("Stage Evaluations")
                for sr in stage_runs:
                    judgment = db.get_judgment_for_stage_run(sr.id)
                    status = "Judged" if judgment else "Pending"
                    st.text(f"• {sr.stage_id}: {len(sr.candidates)} candidates - {status}")


if __name__ == "__main__":
    main()
