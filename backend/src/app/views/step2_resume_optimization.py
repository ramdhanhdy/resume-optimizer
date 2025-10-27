import streamlit as st
from typing import Optional

from src.app.streaming import consume_stream
from src.utils import save_uploaded_file, get_file_icon, cleanup_temp_file
from src.app.services import agents as ag
from src.app.services import persistence as persist
from src.app.views.step2_github_curator import render_github_curator


def render_step(
    *,
    db,
    client,
    model: str,
    auto_run: bool,
    auto_resume_method: Optional[str],
    auto_github_enabled: bool,
    auto_github_username: Optional[str],
    auto_github_token: Optional[str],
) -> None:
    """Render Step 2: Resume Optimization (UI + orchestration)."""
    # Auto-run: trigger optimization immediately if enabled and not yet done
    if (
        st.session_state.auto_run_active
        and not st.session_state.optimization_report
        and not st.session_state.get("pipeline_mode")
    ):
        auto_resume_input = None
        if auto_run:
            if (
                auto_resume_method == "Paste"
                and "auto_resume_text" in st.session_state
                and st.session_state.auto_resume_text
            ):
                auto_resume_input = st.session_state.auto_resume_text
            elif (
                auto_resume_method == "Upload"
                and "auto_resume_upload" in st.session_state
                and st.session_state.auto_resume_upload
            ):
                uploaded_file = st.session_state.auto_resume_upload
                temp_path, file_type = save_uploaded_file(uploaded_file)
                st.session_state.temp_files.append(temp_path)
                auto_resume_input = f"[File: {uploaded_file.name}]"

        if auto_resume_input:
            with st.spinner("🤖 Agent 2 is optimizing your resume (auto-run)..."):
                try:
                    st.markdown("### 🔄 Streaming Response")
                    response_container = st.empty()

                    # Use Agent 2 specific model
                    agent2_model = st.session_state.get("model_agent2", model)

                    stream = ag.stream_optimize_resume(
                        client=client,
                        model=agent2_model,
                        resume_text=auto_resume_input,
                        job_analysis=st.session_state.job_analysis,
                        profile_index=st.session_state.get("profile_index"),
                    )

                    full_response, metadata = consume_stream(response_container, stream)

                    st.session_state.resume_text = auto_resume_input
                    st.session_state.optimization_report = full_response
                    st.session_state.agent_costs.append(metadata.get("cost", 0))
                    st.session_state.total_cost += metadata.get("cost", 0)

                    persist.persist_agent_result(
                        db,
                        application_id=st.session_state.application_id,
                        agent_number=2,
                        agent_name="Resume Optimizer",
                        input_data={
                            "resume": auto_resume_input,
                            "job_analysis": st.session_state.job_analysis,
                        },
                        output_data={"optimized_resume": full_response},
                        metadata=metadata,
                        update_fields={
                            "original_resume_text": auto_resume_input,
                            "total_cost": st.session_state.total_cost,
                        },
                    )

                    st.success("✅ Optimization report complete! (auto-run)")

                    for temp_file in st.session_state.temp_files:
                        cleanup_temp_file(temp_file)
                    st.session_state.temp_files = []

                    # Auto-run GitHub curator (optional)
                    if auto_run and auto_github_enabled and auto_github_username:
                        try:
                            from src.app.views.step2_github_curator import (
                                auto_curate_github,
                            )

                            github_model = st.session_state.get("model_github", model)
                            auto_curate_github(
                                db=db,
                                client=client,
                                model=github_model,
                                github_username=auto_github_username,
                                github_token=auto_github_token,
                            )
                        except Exception as e:  # match legacy behavior (warning-only)
                            st.warning(
                                f"⚠️ GitHub analysis failed (continuing without it): {str(e)}"
                            )

                    st.session_state.current_step = 3
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Auto-run error: {str(e)}")
                    st.session_state.auto_run_active = False

    # Header & context
    st.header("✏️ Step 2: Resume Optimization")
    st.markdown("Upload or paste your resume for optimization")

    # Job analysis summary
    with st.expander("📋 Job Analysis Summary", expanded=False):
        ja = st.session_state.job_analysis
        st.markdown(ja[:1000] + "..." if len(ja) > 1000 else ja)

    # Info section
    with st.expander("ℹ️ What This Agent Does", expanded=False):
        st.markdown(
            """
            The **Resume Optimizer** will:
            - ✅ Provide specific before/after edits
            - ✅ Explain rationale for each change
            - ✅ Align content with job requirements
            - ✅ Integrate ATS keywords naturally
            - ✅ Improve impact statements with metrics
            - ✅ Generate complete optimized resume
            """
        )

    # Input controls
    resume_input_method = st.radio(
        "Input method:", ["Paste Text", "Upload File"], horizontal=True
    )

    uploaded_resume = None

    if resume_input_method == "Paste Text":
        resume_text = st.text_area(
            "Your Resume", height=300, placeholder="Paste your complete resume here..."
        )
    else:
        uploaded_resume = st.file_uploader(
            "Upload Resume",
            type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
            help="File uploads are temporarily disabled. Please paste your resume text instead.",
            disabled=True,
        )
        if uploaded_resume:
            st.success(
                f"{get_file_icon(uploaded_resume.type)} File uploaded: {uploaded_resume.name}"
            )
            resume_text = f"[File: {uploaded_resume.name}]"
        else:
            resume_text = ""

    if st.button("🚀 Optimize Resume", disabled=not resume_text):
        with st.spinner("🤖 Agent 2 is optimizing your resume..."):
            try:
                if resume_input_method == "Upload File" and uploaded_resume:
                    temp_path, file_type = save_uploaded_file(uploaded_resume)
                    st.session_state.temp_files.append(temp_path)
                    resume_input = f"[File: {uploaded_resume.name}]"
                else:
                    resume_input = resume_text

                st.markdown("### 🔄 Streaming Response")
                response_container = st.empty()

                # Use Agent 2 specific model
                agent2_model = st.session_state.get("model_agent2", model)

                stream = ag.stream_optimize_resume(
                    client=client,
                    model=agent2_model,
                    resume_text=resume_input,
                    job_analysis=st.session_state.job_analysis,
                    profile_index=st.session_state.get("profile_index"),
                )

                full_response, metadata = consume_stream(response_container, stream)

                st.session_state.resume_text = resume_input
                st.session_state.optimization_report = full_response
                st.session_state.agent_costs.append(metadata.get("cost", 0))
                st.session_state.total_cost += metadata.get("cost", 0)

                persist.persist_agent_result(
                    db,
                    application_id=st.session_state.application_id,
                    agent_number=2,
                    agent_name="Resume Optimizer",
                    input_data={
                        "resume": resume_input,
                        "job_analysis": st.session_state.job_analysis,
                    },
                    output_data={"optimized_resume": full_response},
                    metadata=metadata,
                    update_fields={
                        "original_resume_text": resume_input,
                        "total_cost": st.session_state.total_cost,
                    },
                )

                st.success("✅ Optimization report complete!")

                for temp_file in st.session_state.temp_files:
                    cleanup_temp_file(temp_file)
                st.session_state.temp_files = []

                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # Optional: curate GitHub projects once job analysis + profile context exist.
    render_github_curator(db=db, client=client, model=model)

    # Auto-advance safeguard: if we have an optimization report and are still on Step 2,
    # advance to Step 3 to continue the flow.
    if (
        st.session_state.get("optimization_report")
        and st.session_state.current_step == 2
    ):
        st.session_state.current_step = 3
        st.rerun()
