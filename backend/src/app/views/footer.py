import streamlit as st


def render_footer() -> None:
    st.markdown("---")
    st.markdown(
        """
<div style="text-align: center; color: #9ca3af; padding: 20px;">
    <p>Built with ❤️ using Streamlit and OpenRouter & LongCat APIs</p>
    <p style="font-size: 12px;">Make sure to review all AI-generated content before submitting applications</p>
</div>
""",
        unsafe_allow_html=True,
    )

