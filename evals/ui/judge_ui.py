"""Streamlit UI for blind candidate comparison and judgment.

This module provides the human evaluation interface for comparing
model outputs and recording preferences.
"""

import streamlit as st
import uuid
from typing import List, Optional

from framework.schemas import StageEval, CandidateOutput
from framework.collector import JudgmentCollector
from framework.analyzer import EvalAnalyzer
from framework.config_resume import (
    get_stage_config,
    get_tags_for_stage,
    get_criteria_for_stage,
    CRITERIA_DESCRIPTIONS,
)
from db.eval_db import EvalDatabase


def render_judge_ui(
    stage_eval: StageEval,
    collector: JudgmentCollector,
    evaluator_id: str = "default",
) -> bool:
    """Render the blind comparison UI for a stage evaluation.

    Args:
        stage_eval: StageEval with candidates to compare
        collector: JudgmentCollector for recording judgments
        evaluator_id: ID of the human evaluator

    Returns:
        True if judgment was submitted
    """
    stage_config = get_stage_config(stage_eval.stage_id)

    st.header(f"Evaluate: {stage_config.display_name}")
    st.caption(stage_config.description)

    # Show context
    with st.expander("Context (Job Posting & Profile Summary)", expanded=False):
        context = stage_eval.context
        if "job_posting" in context:
            st.subheader("Job Posting")
            st.text(context["job_posting"][:2000] + "..." if len(context.get("job_posting", "")) > 2000 else context.get("job_posting", ""))
        if "profile" in context:
            st.subheader("Profile")
            st.text(context["profile"][:2000] + "..." if len(context.get("profile", "")) > 2000 else context.get("profile", ""))

    st.divider()

    # Show candidates side by side
    st.subheader("Compare Outputs")
    st.info(
        "Model identities are hidden. Compare based on the evaluation criteria below."
    )

    candidates = stage_eval.candidates
    num_candidates = len(candidates)

    if num_candidates == 0:
        st.warning("No candidates to evaluate.")
        return False

    # Create columns for side-by-side comparison
    if num_candidates <= 3:
        cols = st.columns(num_candidates)
        for col, cand in zip(cols, candidates):
            with col:
                _render_candidate_card(cand)
    else:
        # For more candidates, use tabs
        tabs = st.tabs([f"Option {c.candidate_label}" for c in candidates])
        for tab, cand in zip(tabs, candidates):
            with tab:
                _render_candidate_card(cand, show_header=False)

    st.divider()

    # Evaluation criteria reference
    with st.expander("Evaluation Criteria", expanded=False):
        criteria = get_criteria_for_stage(stage_eval.stage_id)
        for criterion in criteria:
            desc = CRITERIA_DESCRIPTIONS.get(criterion, "")
            st.markdown(f"**{criterion.replace('_', ' ').title()}**: {desc}")

    st.divider()

    # Judgment form
    st.subheader("Your Judgment")

    # Winner selection
    winner = st.radio(
        "Best output:",
        options=[c.candidate_label for c in candidates],
        horizontal=True,
        key=f"winner_{stage_eval.id}",
    )

    # Optional full ranking
    with st.expander("Full Ranking (optional)", expanded=False):
        st.caption("Drag to reorder from best to worst")
        # Simplified ranking input
        ranking_input = st.text_input(
            "Enter ranking (e.g., 'A, C, B'):",
            key=f"ranking_{stage_eval.id}",
            placeholder="A, B, C",
        )

    # Optional detailed scores
    with st.expander("Detailed Scores (optional)", expanded=False):
        criteria = get_criteria_for_stage(stage_eval.stage_id)
        scores = {}
        for criterion in criteria:
            desc = CRITERIA_DESCRIPTIONS.get(criterion, "")
            scores[criterion] = st.slider(
                f"{criterion.replace('_', ' ').title()}",
                min_value=1,
                max_value=5,
                value=3,
                help=desc,
                key=f"score_{stage_eval.id}_{criterion}",
            )

    # Tags
    available_tags = get_tags_for_stage(stage_eval.stage_id)
    tags = st.multiselect(
        "Tags (optional)",
        options=available_tags,
        key=f"tags_{stage_eval.id}",
    )

    # Comments
    comments = st.text_area(
        "Comments (optional)",
        key=f"comments_{stage_eval.id}",
        placeholder="Any additional observations...",
    )

    # Submit button
    col1, col2 = st.columns([1, 4])
    with col1:
        submitted = st.button(
            "Submit Judgment",
            type="primary",
            key=f"submit_{stage_eval.id}",
        )

    if submitted:
        # Parse ranking if provided
        ranking_labels = None
        if ranking_input:
            ranking_labels = [
                label.strip().upper()
                for label in ranking_input.split(",")
                if label.strip()
            ]

        try:
            collector.record_judgment_by_label(
                stage_eval=stage_eval,
                chosen_label=winner,
                evaluator_id=evaluator_id,
                ranking_labels=ranking_labels,
                scores=scores if any(s != 3 for s in scores.values()) else None,
                tags=tags if tags else None,
                comments=comments if comments else None,
            )
            st.success("Judgment recorded successfully!")
            return True
        except Exception as e:
            st.error(f"Error recording judgment: {e}")
            return False

    return False


def _render_candidate_card(
    candidate: CandidateOutput,
    show_header: bool = True,
) -> None:
    """Render a single candidate output card."""
    if show_header:
        st.markdown(f"### Option {candidate.candidate_label}")

    # Metrics row
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Latency", f"{candidate.latency_ms}ms")
    with col2:
        st.metric("Tokens", f"~{candidate.token_count}")

    # Output text
    # Generate unique key to avoid widget collisions when candidate.id is None
    if candidate.id is not None:
        widget_key = f"output_{candidate.id}"
    elif candidate.candidate_label:
        widget_key = f"output_{candidate.candidate_label}"
    else:
        # Fallback: generate UUID if both id and candidate_label are unavailable
        widget_key = f"output_{uuid.uuid4().hex[:8]}"
    
    st.text_area(
        "Output",
        value=candidate.output_text,
        height=400,
        disabled=True,
        key=widget_key,
        label_visibility="collapsed",
    )


def render_results_dashboard(
    db: EvalDatabase,
    stage_id: str,
) -> None:
    """Render analysis results dashboard.

    Args:
        db: Database with evaluation data
        stage_id: Stage to show results for
    """
    analyzer = EvalAnalyzer(db)
    stage_config = get_stage_config(stage_id)

    st.header(f"Results: {stage_config.display_name}")

    # Win rates
    st.subheader("Win Rates")
    win_rates = analyzer.compute_win_rates(stage_id)

    if not win_rates:
        st.info("No evaluation data yet.")
        return

    # Win rate chart
    import pandas as pd

    df = pd.DataFrame([
        {
            "Model": r.model_id.split("/")[-1],  # Short name
            "Win Rate": r.win_rate,
            "Wins": r.wins,
            "Appearances": r.appearances,
        }
        for r in win_rates
    ])

    st.bar_chart(df.set_index("Model")["Win Rate"])

    # Detailed table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # Bradley-Terry ranking
    st.subheader("Bradley-Terry Ranking")
    try:
        bt_results = analyzer.bradley_terry_ranking(stage_id)
        if bt_results:
            bt_df = pd.DataFrame([
                {
                    "Rank": r.rank,
                    "Model": r.model_id.split("/")[-1],
                    "Strength": f"{r.strength:.3f}",
                }
                for r in bt_results
            ])
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
        else:
            st.caption("Need at least 2 models with pairwise comparisons for Bradley-Terry ranking.")
    except Exception as e:
        st.error(f"Error computing Bradley-Terry ranking: {e}")

    st.divider()

    # Pairwise comparisons
    st.subheader("Pairwise Comparisons")
    try:
        pairwise = analyzer.all_pairwise_comparisons(stage_id)
        if pairwise:
            pw_df = pd.DataFrame([
                {
                    "Model A": r.model_a.split("/")[-1],
                    "Model B": r.model_b.split("/")[-1],
                    "P(A > B)": f"{r.p_a_preferred:.2f}",
                    "95% CI": f"[{r.ci_low:.2f}, {r.ci_high:.2f}]",
                    "Significant": "Yes" if r.significant else "No",
                    "N": r.total,
                }
                for r in pairwise
            ])
            st.dataframe(pw_df, use_container_width=True, hide_index=True)
        else:
            st.caption("Need at least 2 models to show pairwise comparisons.")
    except Exception as e:
        st.error(f"Error computing pairwise comparisons: {e}")

    st.divider()

    # Mean scores
    st.subheader("Mean Scores by Criterion")
    try:
        mean_scores = analyzer.compute_mean_scores(stage_id)
        if mean_scores:
            scores_data = []
            for model, criteria in mean_scores.items():
                row = {"Model": model.split("/")[-1]}
                row.update({k: f"{v:.2f}" for k, v in criteria.items()})
                scores_data.append(row)

            scores_df = pd.DataFrame(scores_data)
            st.dataframe(scores_df, use_container_width=True, hide_index=True)
        else:
            st.caption("No detailed scores recorded. Add scores when judging to see this section.")
    except Exception as e:
        st.error(f"Error computing mean scores: {e}")

    st.divider()

    # Tag frequencies
    st.subheader("Tag Frequencies")
    try:
        tag_freqs = analyzer.compute_tag_frequencies(stage_id)
        if tag_freqs:
            for model, tags in tag_freqs.items():
                st.markdown(f"**{model.split('/')[-1]}**")
                tag_str = ", ".join(f"{tag} ({count})" for tag, count in tags.items())
                st.caption(tag_str)
        else:
            st.caption("No tags recorded. Add tags when judging to see this section.")
    except Exception as e:
        st.error(f"Error computing tag frequencies: {e}")


def render_pending_queue(
    db: EvalDatabase,
    collector: JudgmentCollector,
    evaluator_id: str = "default",
) -> None:
    """Render the queue of pending evaluations.

    Args:
        db: Database with evaluation data
        collector: JudgmentCollector for recording judgments
        evaluator_id: ID of the human evaluator
    """
    st.header("Pending Evaluations")

    pending = db.get_pending_stage_runs(limit=50)

    if not pending:
        st.success("No pending evaluations. All caught up!")
        return

    st.info(f"{len(pending)} evaluations waiting for judgment")

    # Show first pending evaluation
    current = pending[0]
    
    # Header with delete option
    col1, col2 = st.columns([4, 1])
    with col1:
        st.caption(f"Scenario: {current.scenario_id} | Stage: {current.stage_id}")
    with col2:
        if st.button("🗑️ Delete", key=f"delete_{current.id}", type="secondary"):
            db.delete_stage_run(current.id)
            st.success("Deleted evaluation")
            st.rerun()

    submitted = render_judge_ui(current, collector, evaluator_id)

    if submitted:
        st.rerun()

    # Show queue with delete options
    with st.expander(f"Queue ({len(pending) - 1} more)", expanded=False):
        for eval_item in pending[1:10]:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(f"• {eval_item.scenario_id} / {eval_item.stage_id}")
            with col2:
                if st.button("🗑️", key=f"del_{eval_item.id}"):
                    db.delete_stage_run(eval_item.id)
                    st.rerun()
        if len(pending) > 10:
            st.caption(f"... and {len(pending) - 10} more")
        
        # Clear all button
        st.divider()
        if st.button("🗑️ Clear All Pending", type="secondary"):
            for item in pending:
                db.delete_stage_run(item.id)
            st.success(f"Deleted {len(pending)} evaluations")
            st.rerun()
