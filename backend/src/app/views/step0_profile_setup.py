import datetime as dt
import streamlit as st
import json

from src.api import fetch_public_page_text, ExaContentError
from src.app.streaming import consume_stream
from src.app.services import agents as ag
from src.app.services import persistence as persist
from src.agents.github_projects_agent import fetch_github_repos
from src.ui import render_github_repos_cards_with_filters


def render_step(*, db, client, model: str) -> None:
    """Render Step 0: Profile Setup.

    Lets user fetch profile text (e.g., LinkedIn) via Exa and build a
    persistent profile index for downstream agents.
    """
    st.header("Step 0: Profile Setup")
    st.markdown(
        "Connect public sources (e.g., LinkedIn) and build a reusable, evidence-backed profile index."
    )

    with st.expander("What This Does", expanded=False):
        st.markdown(
            """
            - Fetch your public profile text (e.g., LinkedIn) via Exa
            - Build an evidence-aware profile index with conservative phrasing
            - Reuse this index across jobs to propose safe, grounded content
            """
        )

    # Load last saved profile (optional)
    if (
        st.session_state.get("profile_text") == ""
        and st.session_state.get("profile_index") == ""
    ):
        if st.button("Load Last Saved Profile"):
            try:
                rec = persist.load_latest_profile(db)
                if rec:
                    st.session_state.profile_text = rec.get("profile_text", "")
                    st.session_state.profile_index = rec.get("profile_index", "")
                    st.session_state.profile_sources = rec.get("sources", [])
                    st.session_state.profile_last_updated = rec.get(
                        "updated_at"
                    ) or rec.get("created_at")
                    st.success("Loaded last saved profile.")
                else:
                    st.info("No saved profile found.")
            except Exception as exc:
                st.warning(f"Could not load saved profile: {exc}")

    st.markdown(
        "**Recommended order:** 1) Fetch LinkedIn → 2) (Optional) Fetch GitHub → 3) Build Profile Index (Step 2 will handle role-specific curation)."
    )

    # Step 1: LinkedIn source
    st.subheader("Step 1: Fetch LinkedIn profile")
    linkedin_url = st.text_input(
        "LinkedIn Profile URL",
        placeholder="https://www.linkedin.com/in/your-handle/",
        help="Public profile pages only. Requires EXA_API_KEY in your environment.",
    )
    if st.button(
        "1) Fetch LinkedIn via Exa",
        disabled=not linkedin_url.strip(),
        key="btn_fetch_linkedin",
    ):
        try:
            with st.spinner("Fetching profile content..."):
                text = fetch_public_page_text(linkedin_url.strip())
            st.session_state.profile_text = text
            sources = set(st.session_state.get("profile_sources", []) or [])
            sources.add(linkedin_url.strip())
            st.session_state.profile_sources = list(sources)
            st.success("LinkedIn profile content fetched.")
        except (ExaContentError, RuntimeError) as exc:
            st.error(f"Exa error: {exc}")
        except Exception as exc:
            st.error(f"Error fetching profile: {exc}")

    # Optional GitHub ingestion
    st.markdown("---")
    st.subheader("Step 2 (optional): Fetch GitHub repositories")
    gh_user = st.text_input("GitHub Username", placeholder="your-github-username")
    gh_token = st.text_input("GitHub Token (optional)", type="password")
    if st.button(
        "2) Fetch GitHub Repos",
        disabled=not gh_user.strip(),
        key="btn_fetch_github_repos",
    ):
        try:
            with st.spinner("Fetching all repositories..."):
                repos = fetch_github_repos(
                    gh_user.strip(), token=gh_token or None, max_repos=None
                )
            st.session_state.profile_repos = repos
            sources = set(st.session_state.get("profile_sources", []) or [])
            sources.add(f"github:{gh_user.strip()}")
            st.session_state.profile_sources = list(sources)
            st.success("GitHub repositories fetched.")
        except Exception as exc:
            st.error(f"GitHub fetch error: {exc}")

    # Display fetched GitHub repos (toggleable, hidden by default)
    if st.session_state.get("profile_repos"):
        with st.expander("🐙 View Fetched GitHub Repositories", expanded=False):
            render_github_repos_cards_with_filters(
                repos=st.session_state.profile_repos,
                show_readme=True
            )

    st.markdown("---")
    st.subheader("Step 3: Build Profile Index")
    if st.button(
        "3) Build Profile Index",
        disabled=not (
            st.session_state.get("profile_text")
            and len(st.session_state.profile_text.strip()) > 0
        ),
        key="btn_build_index",
    ):
        with st.spinner("Profiling with LLM (streaming)..."):
            container = st.empty()
            profile_model = st.session_state.get("model_profile_agent", model)
            stream = ag.stream_index_profile(
                client=client,
                model=profile_model,
                profile_text=st.session_state.profile_text,
                profile_repos=st.session_state.get("profile_repos"),
            )
            full_response, metadata = consume_stream(container, stream)
            st.session_state.profile_index = full_response
            st.session_state.profile_last_updated = dt.datetime.utcnow().isoformat()
            st.session_state.agent_costs.append(metadata.get("cost", 0))
            st.session_state.total_cost += metadata.get("cost", 0)
            st.success("Profile index created.")
            try:
                persist.save_profile(
                    db,
                    sources=st.session_state.get("profile_sources", []),
                    profile_text=st.session_state.profile_text,
                    profile_index=st.session_state.profile_index,
                )
            except Exception as exc:
                st.warning(f"Saved to session only (DB persistence failed): {exc}")

    st.markdown(
        "> ℹ️ GitHub project curation now happens after job analysis in Step 2 so the agent can tailor selections to the target role. Fetching repos here ensures your profile index already knows about your projects."
    )
    # Preview panels
    if st.session_state.get("profile_text"):
        st.markdown("### Profile Text (preview)")
        preview = st.session_state.profile_text[:1200]
        truncated = len(st.session_state.profile_text) > 1200
        st.code(preview + ("\n... [truncated]" if truncated else ""), language="text")

    if st.session_state.get("profile_index"):
        st.markdown("### Profile Index (latest)")
        st.text_area(
            "profile_index",
            value=st.session_state.profile_index,
            height=240,
            label_visibility="collapsed",
        )

    # Navigation controls
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Skip for now"):
            st.session_state.current_step = 1
            st.rerun()
    with col2:
        if st.button("Proceed to Step 1: Job Analysis"):
            st.session_state.current_step = 1
            st.rerun()
