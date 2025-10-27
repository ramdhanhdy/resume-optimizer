import streamlit as st

from src.app.streaming import consume_stream
from src.ui import render_diff_view
from src.app.services import agents as ag
from src.app.services import persistence as persist
from src.app.services.validation_parser import extract_validation_artifacts


def render_step(*, db, client, model: str) -> None:
    """Render Step 4: Validation & Scoring."""
    # Auto-run validation
    if (
        st.session_state.auto_run_active
        and not st.session_state.validation_result
        and not st.session_state.get("pipeline_mode")
    ):
        with st.spinner("🤖 Agent 4 is validating your resume (auto-run)..."):
            try:
                st.markdown("### 🔄 Streaming Response")
                response_container = st.empty()

                # Use Agent 4 specific model
                agent4_model = st.session_state.get("model_agent4", model)

                stream = ag.stream_validate_resume(
                    client=client,
                    model=agent4_model,
                    optimized_resume=st.session_state.optimized_resume,
                    job_posting=st.session_state.job_posting,
                    job_analysis=st.session_state.job_analysis,
                    profile_index=st.session_state.get("profile_index"),
                )

                full_response, metadata = consume_stream(response_container, stream)

                st.session_state.validation_result = full_response
                st.session_state.agent_costs.append(metadata.get("cost", 0))
                st.session_state.total_cost += metadata.get("cost", 0)

                persist.persist_agent_result(
                    db,
                    application_id=st.session_state.application_id,
                    agent_number=4,
                    agent_name="Validator",
                    input_data={
                        "optimized_resume": st.session_state.optimized_resume,
                        "job_posting": st.session_state.job_posting,
                        "job_analysis": st.session_state.job_analysis,
                    },
                    output_data={"validation": full_response},
                    metadata=metadata,
                    update_fields={"total_cost": st.session_state.total_cost},
                )

                # Parse structured artifacts from the validator output
                parsed_scores, red_flags, recommendations = (
                    extract_validation_artifacts(full_response)
                )

                persist.save_validation_scores(
                    db,
                    application_id=st.session_state.application_id,
                    scores=parsed_scores,
                    red_flags=red_flags,
                    recommendations=recommendations,
                )

                st.success("✅ Validation complete! (auto-run) Proceeding to Step 5...")
                st.session_state.current_step = 5
                st.rerun()

            except Exception as e:
                st.error(f"❌ Auto-run error: {str(e)}")
                st.session_state.auto_run_active = False

    # Normal UI
    st.header("✅ Step 4: Validation & Scoring")
    st.markdown("Validate the optimized resume and get final recommendations")

    with st.expander("ℹ️ What This Agent Does", expanded=False):
        st.markdown(
            """
            The **Validator** will:
            - ✅ Score resume across 5 dimensions (0-100)
            - ✅ Identify critical red flags and risks
            - ✅ Provide quick-win polish suggestions
            - ✅ Assess ATS compatibility
            - ✅ Give final submission readiness verdict
            - ✅ Offer competitive positioning insights
            """
        )

    if "optimization_report" in st.session_state:
        with st.expander("📋 View Full Optimization Report", expanded=False):
            st.markdown(st.session_state.optimization_report)

    st.markdown("### 📊 Resume Comparison")
    render_diff_view(st.session_state.resume_text, st.session_state.optimized_resume)

    if st.button("🚀 Validate Resume"):
        with st.spinner("🤖 Agent 3 is validating your resume..."):
            try:
                st.markdown("### 🔄 Streaming Response")
                response_container = st.empty()

                # Use Agent 4 specific model
                agent4_model = st.session_state.get("model_agent4", model)

                stream = ag.stream_validate_resume(
                    client=client,
                    model=agent4_model,
                    optimized_resume=st.session_state.optimized_resume,
                    job_posting=st.session_state.job_posting,
                    job_analysis=st.session_state.job_analysis,
                    profile_index=st.session_state.get("profile_index"),
                )

                full_response, metadata = consume_stream(response_container, stream)

                st.session_state.validation_result = full_response
                st.session_state.agent_costs.append(metadata.get("cost", 0))
                st.session_state.total_cost += metadata.get("cost", 0)

                persist.persist_agent_result(
                    db,
                    application_id=st.session_state.application_id,
                    agent_number=4,
                    agent_name="Validator",
                    input_data={
                        "optimized_resume": st.session_state.optimized_resume,
                        "job_posting": st.session_state.job_posting,
                        "job_analysis": st.session_state.job_analysis,
                    },
                    output_data={"validation": full_response},
                    metadata=metadata,
                    update_fields={"total_cost": st.session_state.total_cost},
                )

                # Parse structured artifacts from the validator output
                parsed_scores, red_flags, recommendations = (
                    extract_validation_artifacts(full_response)
                )

                persist.save_validation_scores(
                    db,
                    application_id=st.session_state.application_id,
                    scores=parsed_scores,
                    red_flags=red_flags,
                    recommendations=recommendations,
                )

                st.success(
                    "✅ Validation complete! Proceed to Step 5 for final polish and export."
                )
                st.session_state.current_step = 5
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
