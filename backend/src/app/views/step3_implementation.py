import streamlit as st

from src.app.streaming import consume_stream
from src.app.services import agents as ag
from src.app.services import persistence as persist


def render_step(*, db, client, model: str, auto_run: bool | None = None) -> None:
    """Render Step 3: Implement Optimizations."""
    # Auto-run: implement if not done yet
    if (
        st.session_state.auto_run_active
        and not st.session_state.optimized_resume
        and not st.session_state.get("pipeline_mode")
    ):
        with st.spinner("🤖 Agent 3 is implementing optimizations (auto-run)..."):
            try:
                st.markdown("### 🔄 Streaming Response")
                response_container = st.empty()

                optimization_input = st.session_state.optimization_report

                if st.session_state.github_projects_curated:
                    optimization_input += (
                        "\n\n---\n\n## GITHUB PROJECTS CURATOR SUGGESTIONS\n\n"
                    )
                    optimization_input += st.session_state.github_projects_curated
                    optimization_input += "\n\n**IMPORTANT:** Use the GitHub projects suggestions above to enhance/replace the Projects section in the resume."

                # Use Agent 3 specific model
                agent3_model = st.session_state.get("model_agent3", model)

                stream = ag.stream_implement_optimizations(
                    client=client,
                    model=agent3_model,
                    resume_text=st.session_state.resume_text,
                    optimization_report=optimization_input,
                    profile_index=st.session_state.get("profile_index"),
                )

                full_response, metadata = consume_stream(response_container, stream)

                st.session_state.optimized_resume = full_response
                st.session_state.agent_costs.append(metadata.get("cost", 0))
                st.session_state.total_cost += metadata.get("cost", 0)

                persist.persist_agent_result(
                    db,
                    application_id=st.session_state.application_id,
                    agent_number=3,
                    agent_name="Optimizer Implementer",
                    input_data={
                        "resume": st.session_state.resume_text,
                        "optimization_report": st.session_state.optimization_report,
                    },
                    output_data={"optimized_resume": full_response},
                    metadata=metadata,
                    update_fields={
                        "optimized_resume_text": full_response,
                        "total_cost": st.session_state.total_cost,
                    },
                )

                st.success(
                    "✅ Optimized resume generated! (auto-run) Proceeding to Step 4..."
                )
                st.session_state.current_step = 4
                st.rerun()

            except Exception as e:
                st.error(f"❌ Auto-run error: {str(e)}")
                st.session_state.auto_run_active = False

    # Normal UI
    st.header("⚡ Step 3: Implement Optimizations")
    st.markdown("Apply the recommendations to generate your final optimized resume")

    with st.expander("📋 View Full Optimization Report", expanded=False):
        st.markdown(st.session_state.optimization_report)

    if st.session_state.github_projects_curated:
        with st.expander("🐈 GitHub Projects Suggestions", expanded=False):
            st.markdown(st.session_state.github_projects_curated)
            st.info(
                "💡 These suggestions will be automatically included in the implementation"
            )

    with st.expander("ℹ️ What This Agent Does", expanded=False):
        st.markdown(
            """
            The **Optimizer Implementer** will:
            - ✅ Apply ALL recommendations from the report
            - ✅ Restructure sections as specified
            - ✅ Rewrite content with optimized language
            - ✅ Integrate ATS keywords naturally
            - ✅ Produce final, polished resume text
            - ✅ Maintain professional formatting
            """
        )

    if st.button("🚀 Generate Optimized Resume"):
        with st.spinner("🤖 Agent 3 is implementing optimizations..."):
            try:
                st.markdown("### 🔄 Streaming Response")
                response_container = st.empty()

                optimization_input = st.session_state.optimization_report
                if st.session_state.github_projects_curated:
                    optimization_input += (
                        "\n\n---\n\n## GITHUB PROJECTS CURATOR SUGGESTIONS\n\n"
                    )
                    optimization_input += st.session_state.github_projects_curated
                    optimization_input += "\n\n**IMPORTANT:** Use the GitHub projects suggestions above to enhance/replace the Projects section in the resume."

                # Use Agent 3 specific model
                agent3_model = st.session_state.get("model_agent3", model)

                stream = ag.stream_implement_optimizations(
                    client=client,
                    model=agent3_model,
                    resume_text=st.session_state.resume_text,
                    optimization_report=optimization_input,
                    profile_index=st.session_state.get("profile_index"),
                )

                full_response, metadata = consume_stream(response_container, stream)

                st.session_state.optimized_resume = full_response
                st.session_state.agent_costs.append(metadata.get("cost", 0))
                st.session_state.total_cost += metadata.get("cost", 0)

                persist.persist_agent_result(
                    db,
                    application_id=st.session_state.application_id,
                    agent_number=3,
                    agent_name="Optimizer Implementer",
                    input_data={
                        "resume": st.session_state.resume_text,
                        "optimization_report": st.session_state.optimization_report,
                    },
                    output_data={"optimized_resume": full_response},
                    metadata=metadata,
                    update_fields={
                        "optimized_resume_text": full_response,
                        "total_cost": st.session_state.total_cost,
                    },
                )

                st.success(
                    "✅ Optimized resume generated! Proceed to Step 4 for validation."
                )
                st.session_state.current_step = 4
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
