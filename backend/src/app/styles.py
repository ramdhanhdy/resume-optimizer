import streamlit as st

STYLES = """
<style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        font-size: 16px;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }
    .stTextInput input {
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }
    h1, h2, h3 {
        color: #1f2937;
    }
    .success-box {
        padding: 1rem;
        background: #d1fae5;
        border-left: 4px solid #10b981;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background: #fef3c7;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background: #fee2e2;
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
"""


def inject_styles() -> None:
    """Inject app-wide CSS styles into Streamlit."""
    st.markdown(STYLES, unsafe_allow_html=True)
