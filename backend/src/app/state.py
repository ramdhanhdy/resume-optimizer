import streamlit as st
import os
from typing import Any


def initialize_session() -> None:
    """Initialize Streamlit session_state with legacy keys and defaults."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        # Start at Step 0: Profile Setup
        st.session_state.current_step = 0
        st.session_state.job_posting = ""
        st.session_state.job_analysis = ""
        st.session_state.resume_text = ""
        st.session_state.optimization_report = ""
        st.session_state.github_projects_curated = None
        st.session_state.optimized_resume = ""
        st.session_state.validation_result = ""
        st.session_state.final_resume = ""
        st.session_state.agent_costs = []
        st.session_state.total_cost = 0.0
        st.session_state.application_id = None
        st.session_state.temp_files = []
        st.session_state.auto_run_active = False

        # Profile memory (Step 0)
        st.session_state.profile_sources = []  # list[str] of URLs or labels
        st.session_state.profile_text = ""  # raw aggregated text (e.g., LinkedIn)
        st.session_state.profile_repos = []  # GitHub repos metadata list
        st.session_state.profile_index = ""  # agent-produced index JSON/text
        st.session_state.profile_last_updated = None

        # Per-agent model configuration
        default_model = "meituan::LongCat-Flash-Chat"
        st.session_state.model_metadata_extractor = (
            default_model  # Fast model for metadata extraction
        )
        st.session_state.model_profile_agent = (
            default_model  # Profile Agent (Step 0)
        )
        st.session_state.model_agent1 = default_model  # Job Analyzer
        st.session_state.model_agent2 = default_model  # Resume Optimizer
        st.session_state.model_agent3 = default_model  # Optimizer Implementer
        st.session_state.model_agent4 = default_model  # Validator
        st.session_state.model_agent5 = default_model  # Polish & Export
        st.session_state.model_github = default_model  # GitHub Projects Agent
        
        # LongCat-Flash-Thinking specific parameter
        st.session_state.thinking_budget = 10000  # Default thinking budget in tokens


def clear_forward_progress(target_step: int) -> list[str]:
    """Clear all session state data for steps beyond target_step.
    
    When navigating backward, this function clears data from the target step
    and all subsequent steps to maintain data integrity. Cost history and
    database linkage are preserved.
    
    Args:
        target_step: The step to navigate back to (0-5)
        
    Returns:
        List of cleared key names for user notification
    """
    # Define which keys belong to which steps
    # Keys are cleared for target_step and all subsequent steps
    step_keys = {
        0: [],  # Profile data is never cleared when going back
        1: ["job_posting", "job_posting_url", "job_analysis"],
        2: ["resume_text", "optimization_report", "github_projects_curated"],
        3: ["optimized_resume"],
        4: ["validation_result"],
        5: ["final_resume"],
    }
    
    cleared_keys = []
    
    # Clear data from target_step onwards
    for step in range(target_step, 6):
        for key in step_keys.get(step, []):
            if key in st.session_state:
                # Clear the key
                if key == "github_projects_curated":
                    st.session_state[key] = None
                else:
                    st.session_state[key] = ""
                cleared_keys.append(key)
    
    # Disable auto-run to prevent conflicts
    if "auto_run_active" in st.session_state:
        st.session_state.auto_run_active = False
    
    # Disable pipeline mode to prevent auto-execution
    if "pipeline_mode" in st.session_state:
        st.session_state.pipeline_mode = False
    
    return cleared_keys
