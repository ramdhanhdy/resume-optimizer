import os
import streamlit as st
from dotenv import load_dotenv

from src.app.config import apply_page_config
from src.app.styles import inject_styles
from src.app.deps import get_database, get_api_client
from src.app.state import initialize_session, clear_forward_progress
from src.app.views.sidebar import render_sidebar
from src.app.views.footer import render_footer
from src.ui import render_back_button, render_progress_stepper


def run() -> None:
    # Env
    load_dotenv()

    # Page + styles
    apply_page_config()
    inject_styles()

    # State + deps
    initialize_session()
    from src.app.services import persistence as persist

    db = get_database(schema_version=2)
    client = get_api_client()

    # Sidebar (returns selections)
    _sidebar = render_sidebar(db)
    auto_run = _sidebar["auto_run"]
    auto_resume_method = _sidebar["auto_resume_method"]
    auto_github_enabled = _sidebar["auto_github_enabled"]
    auto_github_username = _sidebar["auto_github_username"]
    auto_github_token = _sidebar["auto_github_token"]
    model = _sidebar["model"]
    auto_output_format = _sidebar["auto_output_format"]

    # Main header
    st.title("📄 AI Resume Optimizer")
    st.markdown("Optimize your resume for any job posting using three AI agents")
    st.markdown("---")

    # Attempt to auto-load last saved profile once per session
    if not st.session_state.get("profile_autoloaded"):
        try:
            rec = persist.load_latest_profile(db)
            if (
                rec
                and not st.session_state.get("profile_text")
                and not st.session_state.get("profile_index")
            ):
                st.session_state.profile_text = rec.get("profile_text", "")
                st.session_state.profile_index = rec.get("profile_index", "")
                st.session_state.profile_sources = rec.get("sources", [])
                st.session_state.profile_last_updated = rec.get(
                    "updated_at"
                ) or rec.get("created_at")
        except Exception:
            pass
        st.session_state.profile_autoloaded = True

    # Back button + Stepper (in columns for better layout)
    col_back, col_stepper = st.columns([1, 10])
    
    with col_back:
        # Render back button (only shows if current_step > 0)
        back_clicked = render_back_button(st.session_state.current_step)
    
    with col_stepper:
        # Render progress stepper
        render_progress_stepper(st.session_state.current_step)
    
    # Handle backward navigation
    if back_clicked:
        target_step = st.session_state.current_step - 1
        cleared_keys = clear_forward_progress(target_step)
        st.session_state.current_step = target_step
        
        # Show notification about cleared data
        if cleared_keys:
            st.info(f"ℹ️ Navigated back to Step {target_step}. Cleared data: {', '.join(cleared_keys)}")
        else:
            st.info(f"ℹ️ Navigated back to Step {target_step}")
        
        st.rerun()
    
    st.markdown("---")

    # Optional: centralized auto-run pipeline (disables per-step auto-run)
    if auto_run:
        st.session_state.pipeline_mode = True
        from src.app.pipeline import run_from_current_step

        run_from_current_step(
            db=db,
            client=client,
            model=model,
            auto_resume_method=auto_resume_method,
            auto_github_enabled=auto_github_enabled,
            auto_github_username=auto_github_username,
            auto_github_token=auto_github_token,
            auto_output_format=auto_output_format,
        )
    else:
        st.session_state.pipeline_mode = False

    # Route to current step view
    step = st.session_state.current_step

    if step == 0:
        from src.app.views.step0_profile_setup import render_step as render_step0

        render_step0(db=db, client=client, model=model)

    elif step == 1:
        from src.app.views.step1_job_analysis import render_step as render_step1

        render_step1(db=db, client=client, model=model, auto_run=auto_run)

    elif step == 2:
        from src.app.views.step2_resume_optimization import render_step as render_step2

        render_step2(
            db=db,
            client=client,
            model=model,
            auto_run=auto_run,
            auto_resume_method=auto_resume_method,
            auto_github_enabled=auto_github_enabled,
            auto_github_username=auto_github_username,
            auto_github_token=auto_github_token,
        )

    elif step == 3:
        from src.app.views.step3_implementation import render_step as render_step3

        render_step3(db=db, client=client, model=model)

    elif step == 4:
        from src.app.views.step4_validation import render_step as render_step4

        render_step4(db=db, client=client, model=model)

    elif step == 5:
        from src.app.views.step5_polish_export import render_step as render_step5

        render_step5(
            db=db, client=client, model=model, auto_output_format=auto_output_format
        )

    # Footer
    render_footer()
