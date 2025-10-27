import streamlit as st
from typing import Optional

from src.api import fetch_job_posting_text, ExaContentError
from src.utils import save_uploaded_file, cleanup_temp_file, get_file_icon
from src.app.streaming import consume_stream
from src.app.services import agents as ag
from src.app.services import persistence as persist


def render_step(*, db, client, model: str, auto_run: bool) -> None:
    """Render Step 1: Job Analysis (UI + orchestration).

    Preserves legacy behavior and session_state keys.
    """
    st.header("📋 Step 1: Job Analysis")
    st.markdown("Upload or paste the job posting to analyze")

    # Info section in collapsible expander
    with st.expander("ℹ️ What This Agent Does", expanded=False):
        st.markdown(
            """
            The **Job Analyzer** will:
            - ✅ Extract must-have requirements
            - ✅ Identify preferred qualifications
            - ✅ Find hidden requirements
            - ✅ Analyze company culture
            - ✅ List ATS keywords (prioritized)
            - ✅ Create optimization strategy
            """
        )

    # Single column input
    job_input_method = st.radio(
        "Input method:", ["URL", "Paste Text", "Upload File"], horizontal=True
    )

    uploaded_job = None
    job_url_input = ""
    pasted_job_text = ""

    if job_input_method == "Paste Text":
        pasted_job_text = st.text_area(
            "Job Posting",
            height=300,
            placeholder="Paste the complete job posting here...",
        )
        analyze_disabled = not pasted_job_text.strip()
    elif job_input_method == "Upload File":
        uploaded_job = st.file_uploader(
            "Upload Job Posting",
            type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
            help="Upload your job posting as a PDF, DOCX, or text file. PDFs will be processed using Gemini 2.5 Flash.",
        )
        if uploaded_job:
            st.success(
                f"{get_file_icon(uploaded_job.type)} File uploaded: {uploaded_job.name}"
            )
        analyze_disabled = uploaded_job is None
    else:
        job_url_input = st.text_input(
            "Job Posting URL",
            placeholder="https://www.linkedin.com/jobs/view/1234567890",
            help="Paste a public job posting URL to fetch it via Exa (requires EXA_API_KEY).",
        )
        analyze_disabled = not job_url_input.strip()

    if st.button(
        "🚀 Analyze Job Posting",
        disabled=analyze_disabled,
    ):
        with st.spinner(
            "🤖 Agent 1 is analyzing the job posting (fetching content if needed)..."
        ):
            try:
                # Prepare input
                text_input: Optional[str] = None
                file_input: Optional[str] = None
                file_type_input: Optional[str] = None
                job_url_used: Optional[str] = None

                if job_input_method == "Upload File" and uploaded_job:
                    temp_path = save_uploaded_file(uploaded_job)
                    st.session_state.temp_files.append(temp_path)
                    
                    # Extract text from file (uses Gemini for PDFs)
                    import asyncio
                    from src.utils import extract_text_from_file, is_pdf
                    
                    with st.spinner("📄 Extracting text from file..."):
                        text_input = asyncio.run(extract_text_from_file(temp_path))
                    
                    if is_pdf(uploaded_job.type):
                        st.info("✨ PDF processed using Gemini 2.5 Flash document understanding")
                    
                    file_input = None
                    file_type_input = None
                elif job_input_method == "URL":
                    job_url_used = job_url_input.strip()
                    st.info("Fetching job posting via Exa live crawl...")
                    text_input = fetch_job_posting_text(job_url_used)

                    preview_limit = 1000
                    preview = text_input[:preview_limit].strip()
                    if preview:
                        st.markdown("### 📄 Job Posting Preview (via Exa)")
                        truncated = len(text_input) > preview_limit
                        preview_block = preview + (
                            "\n... [preview truncated]" if truncated else ""
                        )
                        st.code(preview_block, language="text")
                else:
                    text_input = pasted_job_text.strip()

                # Create agent stream and run
                st.markdown("### 🔄 Streaming Response")
                response_container = st.empty()

                # Use Agent 1 specific model
                agent1_model = st.session_state.get("model_agent1", model)
                
                # Get thinking_budget from session state (only used for LongCat-Flash-Thinking)
                thinking_budget = st.session_state.get("thinking_budget")

                stream = ag.stream_analyze_job(
                    client=client,
                    model=agent1_model,
                    job_posting=text_input,
                    file_path=file_input,
                    file_type=file_type_input,
                    profile_index=st.session_state.get("profile_index"),
                    thinking_budget=thinking_budget,
                )

                full_response, metadata = consume_stream(response_container, stream)

                # Save to session
                st.session_state.job_posting = text_input or (
                    f"[File: {uploaded_job.name}]" if uploaded_job else ""
                )
                if job_url_used:
                    st.session_state.job_posting_url = job_url_used
                elif "job_posting_url" in st.session_state:
                    del st.session_state["job_posting_url"]
                st.session_state.job_analysis = full_response
                st.session_state.agent_costs.append(metadata.get("cost", 0))
                st.session_state.total_cost += metadata.get("cost", 0)

                # Create application in database if needed (with LLM metadata extraction)
                metadata_model = st.session_state.get(
                    "model_metadata_extractor", "google/gemini-2.0-flash-exp:free"
                )
                persist.create_application_if_needed(
                    db,
                    job_posting_text=st.session_state.job_posting,
                    client=client,
                    model=metadata_model,
                    job_analysis=full_response,
                )

                # Save agent output and update app
                input_payload = {"job_posting": text_input or "[File uploaded]"}
                if job_url_used:
                    input_payload["job_posting_url"] = job_url_used

                persist.persist_agent_result(
                    db,
                    application_id=st.session_state.application_id,
                    agent_number=1,
                    agent_name="Job Analyzer",
                    input_data=input_payload,
                    output_data={"analysis": full_response},
                    metadata=metadata,
                    update_fields={
                        "total_cost": st.session_state.total_cost,
                        "model_used": agent1_model,
                    },
                )

                st.success("✅ Job analysis complete! Proceed to Step 2.")
                st.session_state.current_step = 2

                # Enable auto-run if checkbox is checked
                if auto_run:
                    st.session_state.auto_run_active = True

                # Cleanup temp files
                for temp_file in st.session_state.temp_files:
                    cleanup_temp_file(temp_file)
                st.session_state.temp_files = []

                st.rerun()

            except (ExaContentError, RuntimeError) as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
