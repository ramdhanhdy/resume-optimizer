import json
import streamlit as st
from typing import Optional

from src.app.streaming import consume_stream
from src.app.services import agents as ag
from src.app.services import persistence as persist


def _merge_curated_projects(*, db, full_response: str) -> None:
    """Merge curated GitHub projects into the profile index and persist."""
    profile_index = st.session_state.get("profile_index")
    if not profile_index:
        return
    try:
        curated = json.loads(full_response)
    except json.JSONDecodeError:
        return
    if not isinstance(curated, dict):
        return
    chosen = curated.get("chosen_projects") or []
    if not isinstance(chosen, list) or not chosen:
        return
    try:
        idx = json.loads(profile_index)
    except json.JSONDecodeError:
        idx = {}
    projects = idx.get("projects")
    if not isinstance(projects, list):
        projects = []
    seen = {(p.get("url"), p.get("name")) for p in projects if isinstance(p, dict)}
    updated = False
    for p in chosen:
        if not isinstance(p, dict):
            continue
        name = p.get("name")
        url = p.get("url")
        if (url, name) in seen:
            continue
        entry = {
            "name": name or "",
            "url": url or "",
            "context": "GitHub Curator",
            "tech": p.get("topics") or [],
            "bullets": p.get("bullets") or [],
            "notes": p.get("why") or "",
        }
        projects.append(entry)
        seen.add((url, name))
        updated = True
    if not updated:
        return
    idx["projects"] = projects
    updated_index = json.dumps(idx, ensure_ascii=False, indent=2)
    st.session_state.profile_index = updated_index
    try:
        persist.save_profile(
            db,
            sources=st.session_state.get("profile_sources", []),
            profile_text=st.session_state.get("profile_text", ""),
            profile_index=updated_index,
        )
    except Exception:
        pass


def render_github_curator(*, db, client, model: str) -> None:
    """Render the optional GitHub projects curator block (manual flow)."""
    st.markdown("---")
    st.markdown("### 🐈 Optional: GitHub Projects Curator")
    st.info(
        "💡 Let AI scan your GitHub and suggest better project matches for this role"
    )

    job_analysis = st.session_state.get("job_analysis")
    if not job_analysis:
        st.warning("Run Step 1 (Job Analysis) before curating GitHub projects.")
        return

    profile_index = st.session_state.get("profile_index")
    if not profile_index:
        st.warning(
            "Complete Step 0 (build your profile index) to unlock GitHub curation."
        )
        return

    resume_context = (
        st.session_state.get("resume_text")
        or st.session_state.get("profile_index")
        or st.session_state.get("profile_text")
        or ""
    )

    # Check if repos were already fetched in Step 0
    profile_repos = st.session_state.get("profile_repos")
    has_cached_repos = profile_repos and len(profile_repos) > 0

    with st.expander("ℹ️ What This Does", expanded=False):
        st.markdown(
            """
            The **GitHub Projects Curator** will:
            - ✅ Analyze your GitHub repositories with AI
            - ✅ Select 2-4 most relevant projects for the target role
            - ✅ Write optimized bullet points for each
            - ✅ Suggest which current projects to replace (if any)
            """
        )

    use_github = st.checkbox("🚀 Enhance resume with my GitHub projects")

    if use_github:
        # Show info if repos are cached from Step 0
        if has_cached_repos:
            st.success(f"✅ Using {len(profile_repos)} repositories from Step 0 (Profile Setup)")
            github_username = "cached"  # Placeholder, won't be used for fetching
            github_token = None
            analyze_disabled = not resume_context
        else:
            st.info("💡 Tip: Fetch repos in Step 0 to skip entering credentials here")
            col1, col2 = st.columns([2, 1])

            with col1:
                github_username = st.text_input(
                    "GitHub Username",
                    placeholder="your-github-username",
                    help="Your GitHub username to scan repositories",
                )

            with col2:
                github_token = st.text_input(
                    "GitHub Token (Optional)",
                    type="password",
                    help="Personal access token for higher rate limits",
                )

            analyze_disabled = not (github_username and resume_context)

        if st.button("🔍 Analyze GitHub Repos", disabled=analyze_disabled):
            with st.spinner("🤖 Scanning your GitHub repositories..."):
                try:
                    st.markdown("### 🔄 Streaming Response")
                    response_container = st.empty()

                    # Use GitHub agent specific model
                    github_model = st.session_state.get("model_github", model)

                    stream = ag.stream_curate_github(
                        client=client,
                        model=github_model,
                        github_username=github_username,
                        resume_text=resume_context,
                        job_analysis=job_analysis,
                        github_token=github_token if github_token else None,
                        repos=profile_repos if has_cached_repos else None,
                    )

                    full_response, metadata = consume_stream(response_container, stream)

                    st.session_state.github_projects_curated = full_response
                    st.session_state.agent_costs.append(metadata.get("cost", 0))
                    st.session_state.total_cost += metadata.get("cost", 0)

                    _merge_curated_projects(db=db, full_response=full_response)

                    st.success("✅ GitHub projects analyzed!")
                    st.info("💡 Review the suggestions above, then proceed to Step 3")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info(
                        "Tip: Check your GitHub username and ensure the repos are accessible"
                    )

    # Proceed button
    if st.button("➡️ Proceed to Step 3: Implementation"):
        st.session_state.current_step = 3
        st.rerun()


def auto_curate_github(
    *,
    db,
    client,
    model: str,
    github_username: str,
    github_token: Optional[str],
) -> None:
    """Auto-run curator: run without interactive controls and update session state."""
    # Check if repos were already fetched in Step 0
    profile_repos = st.session_state.get("profile_repos")
    has_cached_repos = profile_repos and len(profile_repos) > 0
    
    if has_cached_repos:
        st.info(f"🐈 Auto-run: Analyzing {len(profile_repos)} repositories from Step 0...")
    else:
        st.info("🐈 Auto-run: Fetching and analyzing GitHub repositories...")
    
    response_container = st.empty()

    stream = ag.stream_curate_github(
        client=client,
        model=model,
        github_username=github_username,
        resume_text=st.session_state.resume_text,
        job_analysis=st.session_state.job_analysis,
        github_token=github_token if github_token else None,
        repos=profile_repos if has_cached_repos else None,
    )

    full_response, metadata = consume_stream(response_container, stream)

    st.session_state.github_projects_curated = full_response
    st.session_state.agent_costs.append(metadata.get("cost", 0))
    st.session_state.total_cost += metadata.get("cost", 0)

    _merge_curated_projects(db=db, full_response=full_response)

    st.success("✅ GitHub projects analyzed! (auto-run)")
