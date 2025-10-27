"""UI components and visualizations for the Streamlit app."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
import pandas as pd


def render_score_radar_chart(scores: Dict[str, float]):
    """Render radar chart for validation scores.

    Args:
        scores: Dictionary of score dimensions and values (0-100)
    """
    categories = list(scores.keys())
    values = list(scores.values())

    # Close the radar chart by repeating first value
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            fillcolor="rgba(99, 110, 250, 0.2)",
            line=dict(color="rgb(99, 110, 250)", width=2),
            name="Scores",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
                gridcolor="rgba(128, 128, 128, 0.2)",
            ),
            angularaxis=dict(
                gridcolor="rgba(128, 128, 128, 0.2)",
            ),
        ),
        showlegend=False,
        height=400,
        margin=dict(l=80, r=80, t=40, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_score_bars(scores: Dict[str, float]):
    """Render horizontal bar chart for scores.

    Args:
        scores: Dictionary of score dimensions and values (0-100)
    """
    df = pd.DataFrame(
        {"Dimension": list(scores.keys()), "Score": list(scores.values())}
    )

    # Color coding
    colors = []
    for score in df["Score"]:
        if score >= 80:
            colors.append("#10b981")  # Green
        elif score >= 60:
            colors.append("#f59e0b")  # Yellow
        else:
            colors.append("#ef4444")  # Red

    fig = go.Figure(
        go.Bar(
            x=df["Score"],
            y=df["Dimension"],
            orientation="h",
            marker=dict(color=colors),
            text=df["Score"].apply(lambda x: f"{x:.0f}%"),
            textposition="auto",
        )
    )

    fig.update_layout(
        xaxis=dict(range=[0, 100], title="Score (%)"),
        yaxis=dict(title=""),
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_readiness_indicator(overall_score: float):
    """Render traffic-light style readiness indicator.

    Args:
        overall_score: Overall score (0-100)
    """
    if overall_score >= 80:
        color = "🟢"
        status = "Ready to Submit"
        message = "Your resume is well-optimized and ready!"
    elif overall_score >= 60:
        color = "🟡"
        status = "Needs Minor Improvements"
        message = "Address the recommendations below before submitting."
    else:
        color = "🔴"
        status = "Needs Major Improvements"
        message = "Significant changes needed. Review all feedback carefully."

    st.markdown(
        f"""
    <div style="
        padding: 20px;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        margin: 20px 0;
    ">
        <h2 style="margin: 0; font-size: 48px;">{color}</h2>
        <h3 style="margin: 10px 0; font-size: 24px;">{status}</h3>
        <p style="margin: 10px 0; font-size: 18px; font-weight: bold;">{overall_score:.0f}%</p>
        <p style="margin: 0; font-size: 14px;">{message}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_cost_tracker(agent_costs: List[float], total_cost: float):
    """Render cost tracking visualization.

    Args:
        agent_costs: List of costs for each agent
        total_cost: Total cost
    """
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric(
            "Agent 1", f"${agent_costs[0]:.4f}" if len(agent_costs) > 0 else "$0.00"
        )
    with col2:
        st.metric(
            "Agent 2", f"${agent_costs[1]:.4f}" if len(agent_costs) > 1 else "$0.00"
        )
    with col3:
        st.metric(
            "Agent 3", f"${agent_costs[2]:.4f}" if len(agent_costs) > 2 else "$0.00"
        )
    with col4:
        st.metric(
            "Agent 4", f"${agent_costs[3]:.4f}" if len(agent_costs) > 3 else "$0.00"
        )
    with col5:
        st.metric(
            "Agent 5", f"${agent_costs[4]:.4f}" if len(agent_costs) > 4 else "$0.00"
        )
    with col6:
        st.metric("Total", f"${total_cost:.4f}", delta=None)


def render_diff_view(original: str, modified: str):
    """Render side-by-side diff view.

    Args:
        original: Original text
        modified: Modified text
    """
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Original Resume**")
        st.text_area(
            "original", value=original, height=400, label_visibility="collapsed"
        )

    with col2:
        st.markdown("**Optimized Resume**")
        st.text_area(
            "optimized", value=modified, height=400, label_visibility="collapsed"
        )


def render_keyword_tags(keywords: List[str], max_display: int = 50):
    """Render keyword tags with styling.

    Args:
        keywords: List of keywords
        max_display: Maximum number of keywords to display
    """
    display_keywords = keywords[:max_display]

    tags_html = " ".join(
        [
            f'<span style="'
            f"background-color: #e0e7ff; "
            f"color: #4338ca; "
            f"padding: 4px 12px; "
            f"border-radius: 12px; "
            f"margin: 4px; "
            f"display: inline-block; "
            f"font-size: 14px; "
            f'font-weight: 500;">{keyword}</span>'
            for keyword in display_keywords
        ]
    )

    st.markdown(tags_html, unsafe_allow_html=True)

    if len(keywords) > max_display:
        st.caption(f"+ {len(keywords) - max_display} more keywords")


def render_back_button(current_step: int) -> bool:
    """Render a back button for backward navigation.
    
    Args:
        current_step: Current step (0-5)
        
    Returns:
        True if back button was clicked, False otherwise
    """
    # Only show button if not on Step 0
    if current_step <= 0:
        return False
    
    # Create a simple back button with consistent styling
    clicked = st.button(
        "← Back",
        key="nav_back_button",
        help=f"Go back to Step {current_step - 1}",
        use_container_width=False,
    )
    
    return clicked


def render_progress_stepper(current_step: int):
    """Render progress stepper for the pipeline (Step 0-5).

    Args:
        current_step: Current step (0-5)
    """
    steps = [
        ("0", "Profile Setup"),
        ("1", "Job Analysis"),
        ("2", "Optimization Report"),
        ("3", "Implementation"),
        ("4", "Validation"),
        ("5", "Polish & Export"),
    ]

    cols = st.columns(len(steps))

    for _, (col, (num, label)) in enumerate(zip(cols, steps), 1):
        with col:
            step_num = int(num)
            if step_num < current_step:
                # Completed
                st.markdown(
                    f"""
                <div style="text-align: center;">
                    <div style="
                        width: 50px;
                        height: 50px;
                        border-radius: 50%;
                        background: #10b981;
                        color: white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 10px;
                        font-size: 20px;
                        font-weight: bold;
                    ">✓</div>
                    <p style="margin: 0; font-size: 14px; color: #10b981;">{label}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            elif step_num == current_step:
                # Current
                st.markdown(
                    f"""
                <div style="text-align: center;">
                    <div style="
                        width: 50px;
                        height: 50px;
                        border-radius: 50%;
                        background: #3b82f6;
                        color: white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 10px;
                        font-size: 20px;
                        font-weight: bold;
                    ">{num}</div>
                    <p style="margin: 0; font-size: 14px; color: #3b82f6; font-weight: bold;">{label}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                # Pending
                st.markdown(
                    f"""
                <div style="text-align: center;">
                    <div style="
                        width: 50px;
                        height: 50px;
                        border-radius: 50%;
                        background: #e5e7eb;
                        color: #9ca3af;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 10px;
                        font-size: 20px;
                        font-weight: bold;
                    ">{num}</div>
                    <p style="margin: 0; font-size: 14px; color: #9ca3af;">{label}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )


def _get_language_emoji(language: str) -> str:
    """Get emoji for programming language.
    
    Args:
        language: Programming language name
        
    Returns:
        Emoji representing the language
    """
    language_map = {
        "python": "🐍",
        "javascript": "⚛️",
        "typescript": "⚛️",
        "java": "☕",
        "rust": "🦀",
        "go": "🔷",
        "ruby": "💎",
        "php": "🐘",
        "c++": "⚙️",
        "c#": "🔷",
        "swift": "🍎",
        "kotlin": "🟣",
        "r": "📊",
    }
    return language_map.get(language.lower(), "⚙️")


def _get_activity_status(days_ago: int) -> tuple:
    """Get activity status indicator.
    
    Args:
        days_ago: Days since last push
        
    Returns:
        Tuple of (emoji, status_text)
    """
    if days_ago <= 30:
        return "🟢", "Active"
    elif days_ago <= 90:
        return "🟡", "Moderate"
    else:
        return "🔴", "Stale"


def _format_days_ago(days_ago: int) -> str:
    """Format days ago into human readable string.
    
    Args:
        days_ago: Days since last push
        
    Returns:
        Formatted string (e.g., "3 days ago", "2 months ago")
    """
    if days_ago == 0:
        return "today"
    elif days_ago == 1:
        return "1 day ago"
    elif days_ago < 30:
        return f"{days_ago} days ago"
    elif days_ago < 365:
        months = days_ago // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = days_ago // 365
        return f"{years} year{'s' if years > 1 else ''} ago"


def _render_topics_html(topics: List[str]) -> str:
    """Render topic tags as HTML.
    
    Args:
        topics: List of GitHub topics
        
    Returns:
        HTML string for topic tags
    """
    if not topics:
        return ""
    
    # Limit to first 5 topics
    display_topics = topics[:5]
    tags_html = " ".join(
        f'<span style="'
        f'background-color: #e0e7ff; '
        f'color: #4338ca; '
        f'padding: 4px 10px; '
        f'border-radius: 12px; '
        f'margin-right: 6px; '
        f'display: inline-block; '
        f'font-size: 12px; '
        f'font-weight: 500;">{topic}</span>'
        for topic in display_topics
    )
    
    more_text = ""
    if len(topics) > 5:
        more_text = f' <span style="color: #6b7280; font-size: 12px;">+{len(topics) - 5} more</span>'
    
    return f'<div style="margin: 10px 0;">🏷️ {tags_html}{more_text}</div>'


def _render_repo_card(repo: Dict[str, Any], show_readme: bool = True) -> None:
    """Render a single GitHub repository card.
    
    Args:
        repo: Repository dictionary from fetch_github_repos()
        show_readme: Whether to show expandable README section
    """
    name = repo.get("name", "Unknown")
    url = repo.get("url", "#")
    description = repo.get("description", "No description available")
    topics = repo.get("topics", [])
    primary_lang = repo.get("primary_lang")
    stars = repo.get("stars", 0)
    last_push_days = repo.get("last_push_days", 10000)
    readme = repo.get("readme", "")
    
    # Get language emoji and activity status
    lang_emoji = _get_language_emoji(primary_lang) if primary_lang else "⚙️"
    activity_emoji, activity_status = _get_activity_status(last_push_days)
    days_text = _format_days_ago(last_push_days)
    
    # Card HTML
    card_html = f"""
    <div style="
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        background: white;
        transition: all 0.2s;
    ">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 18px; color: #1f2937;">
                📦 {name}
            </h3>
            <span style="font-size: 16px; color: #6b7280;">
                ⭐ {stars}
            </span>
        </div>
        
        <div style="margin-bottom: 10px;">
            <a href="{url}" target="_blank" style="
                color: #3b82f6;
                text-decoration: none;
                font-size: 14px;
            ">🔗 {url}</a>
        </div>
        
        <p style="
            margin: 10px 0;
            color: #4b5563;
            font-size: 14px;
            line-height: 1.5;
        ">
            📝 {description[:200]}{"..." if len(description) > 200 else ""}
        </p>
        
        {_render_topics_html(topics)}
        
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
            font-size: 13px;
            color: #6b7280;
        ">
            <span>
                {lang_emoji} {primary_lang or "Unknown"}
            </span>
            <span>
                {activity_emoji} Updated {days_text}
            </span>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # README expander
    if show_readme and readme:
        with st.expander("📄 View README", expanded=False):
            # Truncate README for performance
            readme_preview = readme[:2000]
            if len(readme) > 2000:
                readme_preview += "\n\n... [README truncated for performance]"
            st.markdown(readme_preview)


def render_github_repos_cards(
    repos: List[Dict[str, Any]], 
    show_readme: bool = True,
    columns: int = 2
) -> None:
    """Render GitHub repositories as interactive cards.
    
    Args:
        repos: List of repository dictionaries from fetch_github_repos()
        show_readme: Whether to include expandable README sections
        columns: Number of columns for card layout (1 or 2)
    """
    import json
    
    if not repos:
        st.info("No repositories fetched yet.")
        return
    
    # Summary header
    total_stars = sum(r.get("stars", 0) for r in repos)
    languages = {r.get("primary_lang") for r in repos if r.get("primary_lang")}
    languages_text = ", ".join(sorted(languages)) if languages else "Various"
    
    st.markdown(f"""
    ### 🐙 GitHub Repositories
    📊 **{len(repos)} repositories** | ⭐ **{total_stars} total stars** | 🔵 **Languages:** {languages_text}
    """)
    
    # Optional: Add view toggle
    col1, col2 = st.columns([3, 1])
    with col2:
        view_mode = st.radio(
            "View:", 
            ["Cards", "JSON"], 
            horizontal=True,
            label_visibility="collapsed",
            key="github_repos_view_mode"
        )
    
    if view_mode == "JSON":
        # Fallback JSON view for debugging
        st.code(
            json.dumps(repos, ensure_ascii=False, indent=2),
            language="json"
        )
        return
    
    # Display cards
    st.markdown("---")
    
    if columns == 2:
        # Two-column layout
        for i in range(0, len(repos), 2):
            col1, col2 = st.columns(2)
            
            with col1:
                if i < len(repos):
                    _render_repo_card(repos[i], show_readme)
            
            with col2:
                if i + 1 < len(repos):
                    _render_repo_card(repos[i + 1], show_readme)
    else:
        # Single-column layout
        for repo in repos:
            _render_repo_card(repo, show_readme)


def render_github_repos_cards_with_filters(
    repos: List[Dict[str, Any]], 
    show_readme: bool = True
) -> None:
    """Render GitHub repositories with sorting and filtering options.
    
    Args:
        repos: List of repository dictionaries from fetch_github_repos()
        show_readme: Whether to include expandable README sections
    """
    if not repos:
        st.info("No repositories fetched yet.")
        return
    
    # Extract unique languages
    languages = sorted({r.get("primary_lang") for r in repos if r.get("primary_lang")})
    
    # Filters row
    col1, col2 = st.columns([2, 3])
    
    with col1:
        sort_by = st.selectbox(
            "Sort by:",
            [
                "Stars (High to Low)",
                "Recently Updated",
                "Name (A-Z)",
                "Language"
            ],
            key="github_sort"
        )
    
    with col2:
        if languages:
            selected_langs = st.multiselect(
                "Filter by language:",
                options=languages,
                default=[],
                key="github_lang_filter"
            )
        else:
            selected_langs = []
    
    # Apply filters
    filtered_repos = repos
    if selected_langs:
        filtered_repos = [
            r for r in filtered_repos 
            if r.get("primary_lang") in selected_langs
        ]
    
    # Apply sorting
    if sort_by == "Stars (High to Low)":
        filtered_repos = sorted(
            filtered_repos, 
            key=lambda r: r.get("stars", 0), 
            reverse=True
        )
    elif sort_by == "Recently Updated":
        filtered_repos = sorted(
            filtered_repos, 
            key=lambda r: r.get("last_push_days", 10000)
        )
    elif sort_by == "Name (A-Z)":
        filtered_repos = sorted(
            filtered_repos, 
            key=lambda r: r.get("name", "").lower()
        )
    elif sort_by == "Language":
        filtered_repos = sorted(
            filtered_repos, 
            key=lambda r: r.get("primary_lang", "").lower()
        )
    
    # Show count if filtered
    if len(filtered_repos) < len(repos):
        st.info(f"Showing {len(filtered_repos)} of {len(repos)} repositories")
    
    # Render cards
    render_github_repos_cards(filtered_repos, show_readme, columns=2)
