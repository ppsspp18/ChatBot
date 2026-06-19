import streamlit as st

from api_client import create_mode, delete_mode, edit_mode, get_modes
from state import go_to


def render_modes_page() -> None:
    st.title("🎭 Modes")

    if st.button("⬅ Back to chat"):
        go_to("chat")
        st.rerun()

    st.markdown("---")
    _render_create_form()

    st.markdown("---")
    st.subheader("Existing modes")
    _render_mode_list()


def _render_create_form() -> None:
    with st.expander("➕ Create a new mode"):
        with st.form("create_mode_form"):
            title = st.text_input("Title")
            description = st.text_area("Description")
            system_prompt = st.text_area("System prompt")
            submitted = st.form_submit_button("Create")

            if submitted:
                if not title or not system_prompt:
                    st.error("Title and system prompt are required.")
                else:
                    try:
                        create_mode(title, description, system_prompt)
                        st.success("Mode created.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create mode: {e}")


def _render_mode_list() -> None:
    try:
        modes = get_modes()
    except Exception as e:
        st.error(f"Couldn't load modes: {e}")
        return

    if not modes:
        st.caption("No modes yet.")
        return

    for mode in modes:
        with st.expander(mode["title"]):
            editing_key = f"editing_mode_{mode['mode_id']}"

            if st.session_state.get(editing_key):
                _render_edit_form(mode, editing_key)
            else:
                st.caption(mode["description"])
                st.code(mode["system_prompt"], language=None)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"edit_btn_{mode['mode_id']}", use_container_width=True):
                        st.session_state[editing_key] = True
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"del_btn_{mode['mode_id']}", use_container_width=True):
                        try:
                            delete_mode(mode["mode_id"])
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete mode: {e}")


def _render_edit_form(mode: dict, editing_key: str) -> None:
    with st.form(f"edit_mode_form_{mode['mode_id']}"):
        title = st.text_input("Title", value=mode["title"])
        description = st.text_area("Description", value=mode["description"])
        system_prompt = st.text_area("System prompt", value=mode["system_prompt"])

        col1, col2 = st.columns(2)
        with col1:
            save = st.form_submit_button("Save", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if save:
            try:
                edit_mode(mode["mode_id"], title, description, system_prompt)
                st.session_state[editing_key] = False
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update mode: {e}")

        if cancel:
            st.session_state[editing_key] = False
            st.rerun()
