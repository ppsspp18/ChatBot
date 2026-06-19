import streamlit as st

from api_client import create_conversation, get_conversations, get_modes
from config import PROVIDERS, PROVIDERS_MODELS
from state import go_to, set_current_session


def render_sidebar() -> None:
    st.sidebar.title("💬 Chats")

    if st.sidebar.button("➕ New chat", use_container_width=True):
        st.session_state.show_new_chat_form = True

    if st.session_state.show_new_chat_form:
        _render_new_chat_form()

    st.sidebar.markdown("---")
    st.sidebar.caption("Conversations")
    _render_conversation_list()

    st.sidebar.markdown("---")
    if st.sidebar.button("🎭 Manage modes", use_container_width=True):
        go_to("modes")
        st.rerun()


def _render_new_chat_form() -> None:
    # NOTE: `provider` lives OUTSIDE the form on purpose. Widgets inside an
    # st.form() are batched and don't trigger a script rerun until the form
    # is submitted, so a "Model" selectbox that depends on `provider` would
    # keep showing the *previous* provider's models until Create was
    # clicked (this was the "models don't update" bug). Selectboxes outside
    # a form rerun immediately on change, so keeping provider here keeps
    # the model list inside the form always in sync.
    provider = st.sidebar.selectbox("Provider", PROVIDERS, key="new_chat_provider")

    with st.sidebar.form("new_chat_form"):
        st.write("**Start a new conversation**")

        model = st.selectbox("Model", PROVIDERS_MODELS[provider])

        mode_options = {"(none)": None}
        try:
            for mode in get_modes():
                mode_options[mode["title"]] = mode["mode_id"]
        except Exception:
            pass  # mode selection is optional; fall back to "(none)" only
        mode_label = st.selectbox("Mode", list(mode_options.keys()))

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Create", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if submitted:
            try:
                conversation = create_conversation(
                    # Backend only auto-generates a title when it sees the
                    # exact string "NEW CONVERSATION" (see send_message);
                    # the previous "New Conversation" casing silently
                    # disabled that feature for every new chat.
                    title="NEW CONVERSATION",
                    provider=provider,
                    model=model,
                    mode_id=mode_options[mode_label],
                )
                st.session_state.show_new_chat_form = False
                set_current_session(conversation["session_id"])
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Failed to create conversation: {e}")

        if cancelled:
            st.session_state.show_new_chat_form = False
            st.rerun()


def _render_conversation_list() -> None:
    try:
        conversations = get_conversations()
    except Exception as e:
        st.sidebar.error(f"Couldn't load conversations: {e}")
        return

    if not conversations:
        st.sidebar.caption("No conversations yet.")
        return

    conversations = sorted(
        conversations, key=lambda c: c.get("updated_at", ""), reverse=True
    )

    for conv in conversations:
        is_active = conv["session_id"] == st.session_state.current_session_id
        label = ("▶ " if is_active else "") + conv["title"]
        if st.sidebar.button(label, key=f"conv_{conv['session_id']}", use_container_width=True):
            set_current_session(conv["session_id"])
            st.rerun()
