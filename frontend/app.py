import streamlit as st

from ui import render_sidebar
from api_client import get_response, get_response_stream

st.set_page_config(page_title="LLM Chat", page_icon="💬", layout="centered")
st.title("💬 LLM Chatbot")

stream_mode = render_sidebar()

if "history" not in st.session_state:
    st.session_state.history = []

# Replay existing chat history
for role, text in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)

prompt = st.chat_input("Type your message...")

if prompt:
    st.session_state.history.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if stream_mode:
            placeholder = st.empty()
            full_text = ""
            try:
                for chunk in get_response_stream(prompt):
                    full_text += chunk
                    placeholder.markdown(full_text)
            except Exception as e:
                full_text = f"⚠️ Error contacting backend: {e}"
                placeholder.markdown(full_text)
        else:
            with st.spinner("Thinking..."):
                try:
                    full_text = get_response(prompt)
                except Exception as e:
                    full_text = f"⚠️ Error contacting backend: {e}"
            st.markdown(full_text)

    st.session_state.history.append(("assistant", full_text))