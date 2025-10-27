import streamlit as st


def apply_page_config() -> None:
    """Apply Streamlit page configuration.

    Preserves the existing page settings from the legacy app.py.
    """
    st.set_page_config(
        page_title="Resume Optimizer",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )
