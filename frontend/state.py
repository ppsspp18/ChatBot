import streamlit as st


def init_state() -> None:
    defaults = {
        "page": "chat",                 
        "current_session_id": None,
        "show_new_chat_form": False,
        "editing_conversation": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to(page: str) -> None:
    st.session_state.page = page


def set_current_session(session_id: str) -> None:
    st.session_state.current_session_id = session_id
    st.session_state.editing_conversation = False
    st.session_state.page = "chat"
