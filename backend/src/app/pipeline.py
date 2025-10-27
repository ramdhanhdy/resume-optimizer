"""Auto-run pipeline orchestrator.

Orchestrates the remaining steps when auto-run is enabled, starting from the
current_step and proceeding until completion or until required inputs are
missing. This centralizes the multi-step automation without changing the
one-page wizard UI.
"""

from __future__ import annotations

from typing import Optional
import streamlit as st

from src.app.streaming import consume_stream
from src.app.services import agents as ag
from src.app.services import persistence as persist
from src.app.services.validation_parser import extract_validation_artifacts


def run_from_current_step(
    *,
    db,
    client,
    model: str,
    auto_resume_method: Optional[str],
    auto_github_enabled: bool,
    auto_github_username: Optional[str],
    auto_github_token: Optional[str],
    auto_output_format: Optional[str],
) -> None:
    """Run remaining steps automatically from the current step.

    Safe to call repeatedly; it advances steps only when inputs are ready.
    """
    if not st.session_state.get("auto_run_active"):
        return

    # Prevent infinite loops; at most run the remaining steps once per call
    max_hops = 5
    hops = 0

    while hops < max_hops and st.session_state.get("auto_run_active", False):
        hops += 1
        step = st.session_state.get("current_step", 1)

        # Step 2: Resume Optimization
        if step == 2 and not st.session_state.get("optimization_report"):
            resume_input = None
            if auto_resume_method == "Paste" and st.session_state.get(
                "auto_resume_text"
            ):
                resume_input = st.session_state.auto_resume_text
            elif (
                auto_resume_method == "Upload"
                and st.session_state.get("auto_resume_upload") is not None
            ):
                uploaded_file = st.session_state.auto_resume_upload
                from src.utils import save_uploaded_file, extract_text_from_file
                import asyncio

                temp_path = save_uploaded_file(uploaded_file)
                st.session_state.temp_files.append(temp_path)
                
                # Extract text from file (uses Gemini for PDFs)
                resume_input = asyncio.run(extract_text_from_file(temp_path))

            if not resume_input:
                # Inputs not ready; exit and let UI gather them
                break

            with st.spinner(
                "🤖 Agent 2 is optimizing your resume (auto-run via pipeline)..."
            ):
                response_container = st.empty()
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

                if auto_github_enabled and auto_github_username:
                    try:
                        # Check if repos were already fetched in Step 0
                        profile_repos = st.session_state.get("profile_repos")
                        has_cached_repos = profile_repos and len(profile_repos) > 0
                        
                        github_model = st.session_state.get("model_github", model)
                        gh_container = st.empty()
                        
                        if has_cached_repos:
                            st.info(f"🐈 Using {len(profile_repos)} repositories from Step 0")
                        
                        gh_stream = ag.stream_curate_github(
                            client=client,
                            model=github_model,
                            github_username=auto_github_username,
                            resume_text=st.session_state.resume_text,
                            job_analysis=st.session_state.job_analysis,
                            github_token=auto_github_token
                            if auto_github_token
                            else None,
                            repos=profile_repos if has_cached_repos else None,
                        )
                        gh_full, gh_meta = consume_stream(gh_container, gh_stream)
                        st.session_state.github_projects_curated = gh_full
                        st.session_state.agent_costs.append(gh_meta.get("cost", 0))
                        st.session_state.total_cost += gh_meta.get("cost", 0)
                    except Exception as exc:
                        st.warning(f"GitHub curator failed: {exc}")

                # Advance
                st.session_state.current_step = 3
                continue

        # Step 3: Implement Optimizations
        if step == 3 and not st.session_state.get("optimized_resume"):
            with st.spinner(
                "🤖 Agent 3 is implementing optimizations (auto-run via pipeline)..."
            ):
                response_container = st.empty()
                optimization_input = st.session_state.optimization_report
                if st.session_state.get("github_projects_curated"):
                    optimization_input += (
                        "\n\n---\n\n## GITHUB PROJECTS CURATOR SUGGESTIONS\n\n"
                    )
                    optimization_input += st.session_state.github_projects_curated
                    optimization_input += "\n\n**IMPORTANT:** Use the GitHub projects suggestions above to enhance/replace the Projects section in the resume."
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

                st.session_state.current_step = 4
                continue

        # Step 4: Validation
        if step == 4 and not st.session_state.get("validation_result"):
            with st.spinner(
                "🤖 Agent 4 is validating your resume (auto-run via pipeline)..."
            ):
                response_container = st.empty()
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

                scores, red_flags, recommendations = extract_validation_artifacts(
                    full_response
                )

                persist.save_validation_scores(
                    db,
                    application_id=st.session_state.application_id,
                    scores=scores,
                    red_flags=red_flags,
                    recommendations=recommendations,
                )

                st.session_state.current_step = 5
                continue

        # Step 5: Polish & Export
        if step == 5 and not st.session_state.get("final_resume"):
            format_type = (
                "docx"
                if auto_output_format == "DOCX"
                else "html"
                if auto_output_format
                else "html"
            )
            with st.spinner(
                "🤖 Agent 5 is applying final polish (auto-run via pipeline)..."
            ):
                response_container = st.empty()
                agent5_model = st.session_state.get("model_agent5", model)
                stream = ag.stream_polish_resume(
                    client=client,
                    model=agent5_model,
                    optimized_resume=st.session_state.optimized_resume,
                    validation_report=st.session_state.validation_result,
                    output_format=format_type,
                )
                full_response, metadata = consume_stream(response_container, stream)

                cleaned = _clean_backticks(full_response)
                st.session_state.final_resume = cleaned
                st.session_state.agent_costs.append(metadata.get("cost", 0))
                st.session_state.total_cost += metadata.get("cost", 0)

                persist.persist_agent_result(
                    db,
                    application_id=st.session_state.application_id,
                    agent_number=5,
                    agent_name="Polish Agent",
                    input_data={
                        "optimized_resume": st.session_state.optimized_resume,
                        "validation_report": st.session_state.validation_result,
                    },
                    output_data={"final_resume": full_response},
                    metadata=metadata,
                    update_fields={
                        "optimized_resume_text": full_response,
                        "total_cost": st.session_state.total_cost,
                        "status": "completed",
                    },
                )

                # Done
                st.session_state.auto_run_active = False
                break

        # If none of the above matched, nothing to do now
        break


def _clean_backticks(content: str) -> str:
    content = content.strip()
    if content.startswith("```html"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()
