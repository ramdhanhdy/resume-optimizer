import os
import streamlit as st
from typing import Any, Dict, Optional
from src.ui import render_progress_stepper


def _model_select(
    label: str,
    *,
    session_key: str,
    widget_key: str,
    default: str,
    options: list[str],
    help_text: str,
) -> None:
    """Render a selectbox for model configuration while preserving custom entries."""
    current_value = st.session_state.get(session_key, default)

    choices = options.copy()
    if current_value and current_value not in choices:
        choices.insert(0, current_value)

    selected = st.selectbox(
        label,
        options=choices,
        index=choices.index(current_value) if current_value in choices else 0,
        help=help_text,
        key=widget_key,
    )
    st.session_state[session_key] = selected


def render_sidebar(db) -> Dict[str, Any]:
    """Render the entire sidebar (app info + settings) and return selections.

    Returns keys (also mirrored in st.session_state when widgets use explicit keys):
    - auto_run: bool
    - auto_resume_method: Optional[str]
    - auto_github_enabled: bool
    - auto_github_username: Optional[str]
    - auto_github_token: Optional[str]
    - model: str
    - auto_output_format: Optional[str]  # "HTML" or "DOCX" when auto_run is True
    """
    with st.sidebar:
        st.markdown("# 📄 Resume Optimizer")
        st.markdown("---")

        st.markdown("### 📋 Current Application")
        if st.session_state.application_id:
            st.info(f"Application ID: {st.session_state.application_id}")
        else:
            st.warning("No application started yet")

        st.markdown(f"**Step:** {st.session_state.current_step} of 5")
        st.progress(st.session_state.current_step / 5)

        st.markdown("---")
        st.markdown("### 💰 Cost Tracking")
        st.metric("Session Total", f"${st.session_state.total_cost:.4f}")
        st.metric("All Time", f"${db.get_total_spent():.4f}")

        st.markdown("---")
        st.markdown("### 📚 Recent Applications")
        recent_apps = db.get_all_applications(limit=10)
        if recent_apps:
            for app in recent_apps:
                # Create a better display label
                company = (
                    app["company_name"] if app["company_name"] else "Unknown Company"
                )
                job_title = app["job_title"] if app["job_title"] else "Unknown Position"

                # Truncate intelligently
                max_company_len = 25
                max_title_len = 30

                if len(company) > max_company_len:
                    company_display = company[:max_company_len] + "..."
                else:
                    company_display = company

                if len(job_title) > max_title_len:
                    title_display = job_title[:max_title_len] + "..."
                else:
                    title_display = job_title

                # Status emoji
                status_emoji = "✅" if app.get("status") == "completed" else "🔄"

                expander_label = f"{status_emoji} {company_display} - {title_display}"

                with st.expander(expander_label):
                    st.markdown(f"**Company:** {company}")
                    st.markdown(f"**Position:** {job_title}")
                    st.markdown(f"**Created:** {app['created_at'][:10]}")
                    st.markdown(f"**Status:** {app.get('status', 'in_progress')}")
                    st.markdown(f"**Cost:** ${app['total_cost']:.4f}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(
                            "📥 Load", key=f"load_{app['id']}", use_container_width=True
                        ):
                            st.info("Loading saved application...")
                            # TODO: Implement application loading
                    with col2:
                        if st.button(
                            "Delete",
                            key=f"delete_{app['id']}",
                            use_container_width=True,
                        ):
                            try:
                                db.delete_application(app["id"])
                                if st.session_state.get("application_id") == app["id"]:
                                    for reset_key in [
                                        "application_id",
                                        "job_posting",
                                        "job_analysis",
                                        "resume_text",
                                        "optimization_report",
                                        "optimized_resume",
                                        "validation_result",
                                        "final_resume",
                                        "agent_costs",
                                        "total_cost",
                                    ]:
                                        if reset_key == "agent_costs":
                                            st.session_state[reset_key] = []
                                        elif reset_key == "total_cost":
                                            st.session_state[reset_key] = 0.0
                                        else:
                                            st.session_state[reset_key] = ""
                                st.success("Application deleted.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Failed to delete application: {exc}")

        st.markdown("---")
        st.markdown("### ⚙️ Settings")

        auto_run = st.checkbox(
            "Auto-run remaining steps",
            value=st.session_state.get("auto_run_active", False),
            help="Automatically progress through steps when inputs are ready.",
            key="auto_run_toggle",
        )

        auto_resume_method = st.selectbox(
            "Resume Source for Auto-Run (Step 2)",
            ["Use Uploaded/Pasted", "Use Profile Index"],
            help="When auto-run is enabled, choose which resume source to use at Step 2.",
            key="auto_resume_method",
        )

        auto_github_enabled = st.checkbox(
            "Include GitHub Projects Agent",
            value=False,
            help="Run the optional GitHub Projects Agent after Step 2",
            key="auto_github_enabled",
        )

        auto_github_username: Optional[str] = None
        auto_github_token: Optional[str] = None
        if auto_github_enabled:
            auto_github_username = st.text_input(
                "GitHub Username (for optional projects agent)", key="github_username"
            )
            auto_github_token = st.text_input(
                "GitHub Token (optional)", type="password", key="github_token"
            )

        st.markdown("---")
        st.markdown("### 🤖 Models")

        with st.expander("Per-Agent Model Configuration", expanded=False):
            metadata_options = [
                "meituan::LongCat-Flash-Chat",
                "openrouter::x-ai/grok-4-fast",
                "zenmux::google/gemini-2.5-flash",
            ]
            profile_options = [
                "meituan::LongCat-Flash-Chat",
                "openrouter::qwen/qwen3-max",
                "openrouter::anthropic/claude-sonnet-4.5",
                "openrouter::openai/gpt-5",
                "zenmux::openai/gpt-5",
                "zenmux::google/gemini-2.5-pro",
                "zenmux::google/gemini-2.5-flash",
                "zenmux::anthropic/claude-sonnet-4.5",
                "zenmux::moonshotai/kimi-k2-0905",
            ]
            agent_core_options = [
                "meituan::LongCat-Flash-Chat",
                "meituan::LongCat-Flash-Thinking",
                "openrouter::qwen/qwen3-max",
                "openrouter::anthropic/claude-sonnet-4.5",
                "openrouter::openai/gpt-5",
                "zenmux::openai/gpt-5",
                "zenmux::anthropic/claude-sonnet-4.5",
                "zenmux::google/gemini-2.5-pro",
                "zenmux::moonshotai/kimi-k2-0905",
            ]

            github_options = [
                "meituan::LongCat-Flash-Chat",
                "meituan::LongCat-Flash-Thinking",
                "openrouter::qwen/qwen3-max",
                "openrouter::openai/gpt-5",
                "zenmux::openai/gpt-5",
                "zenmux::moonshotai/kimi-k2-0905",
                "zenmux::google/gemini-2.5-flash",
            ]

            _model_select(
                "Metadata Extractor",
                session_key="model_metadata_extractor",
                widget_key="input_model_metadata",
                default="meituan::LongCat-Flash-Chat",
                options=metadata_options,
                help_text="Fast model for extracting company name and job title",
            )

            _model_select(
                "Profile Agent (Step 0)",
                session_key="model_profile_agent",
                widget_key="input_model_profile_agent",
                default="meituan::LongCat-Flash-Chat",
                options=profile_options,
                help_text="Model for building the reusable profile index",
            )

            _model_select(
                "Agent 1: Job Analyzer",
                session_key="model_agent1",
                widget_key="input_model_agent1",
                default="meituan::LongCat-Flash-Chat",
                options=agent_core_options,
                help_text="Model for analyzing job postings",
            )

            _model_select(
                "Agent 2: Resume Optimizer",
                session_key="model_agent2",
                widget_key="input_model_agent2",
                default="meituan::LongCat-Flash-Chat",
                options=agent_core_options,
                help_text="Model for creating optimization strategy",
            )

            _model_select(
                "Agent 3: Optimizer Implementer",
                session_key="model_agent3",
                widget_key="input_model_agent3",
                default="meituan::LongCat-Flash-Chat",
                options=agent_core_options,
                help_text="Model for implementing optimizations",
            )

            _model_select(
                "Agent 4: Validator",
                session_key="model_agent4",
                widget_key="input_model_agent4",
                default="meituan::LongCat-Flash-Chat",
                options=agent_core_options,
                help_text="Model for validating resume",
            )

            _model_select(
                "Agent 5: Polish & Export",
                session_key="model_agent5",
                widget_key="input_model_agent5",
                default="meituan::LongCat-Flash-Chat",
                options=agent_core_options,
                help_text="Model for final polish",
            )

            _model_select(
                "GitHub Projects Agent",
                session_key="model_github",
                widget_key="input_model_github",
                default="meituan::LongCat-Flash-Chat",
                options=github_options,
                help_text="Model for curating GitHub projects",
            )

            if st.button("🔄 Reset to Defaults"):
                default_model = "meituan::LongCat-Flash-Chat"
                st.session_state.model_metadata_extractor = default_model
                st.session_state.model_profile_agent = default_model
                st.session_state.model_agent1 = default_model
                st.session_state.model_agent2 = default_model
                st.session_state.model_agent3 = default_model
                st.session_state.model_agent4 = default_model
                st.session_state.model_agent5 = default_model
                st.session_state.model_github = default_model
                st.rerun()

        # Keep backward compatibility - use Agent 1 model as default
        model = st.session_state.model_agent1

        if auto_run:
            st.markdown("**Output Format for Step 5:**")
            auto_output_format = st.radio(
                "Final format:",
                ["DOCX", "HTML"],
                help="Choose format for final polished resume",
                key="auto_output_format",
            )
        else:
            auto_output_format = None

    return {
        "auto_run": auto_run,
        "auto_resume_method": auto_resume_method,
        "auto_github_enabled": auto_github_enabled,
        "auto_github_username": auto_github_username,
        "auto_github_token": auto_github_token,
        "model": model,
        "auto_output_format": auto_output_format,
    }
