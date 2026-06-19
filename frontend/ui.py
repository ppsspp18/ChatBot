import streamlit as st


def render_sidebar() -> bool:
    """
    Renders the settings sidebar.
    Returns True if streaming mode is enabled, False otherwise.
    """
    st.sidebar.title("⚙️ Settings")

    stream_mode = st.sidebar.toggle("Enable streaming", value=True)

    st.sidebar.markdown("---")
    st.sidebar.caption("Backend models")
    st.sidebar.write("**Non-stream model:** `gemma3:1b`")
    st.sidebar.write("**Stream model:** `deepseek-r1:1.5b`")

    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear chat history"):
        st.session_state.history = []
        st.rerun()

    return stream_mode
