import streamlit as st

from api_client import get_conversation, get_messages, get_modes, send_message_stream, update_conversation


def render_chat_page() -> None:
    session_id = st.session_state.current_session_id

    if not session_id:
        st.info("Select a conversation from the sidebar, or start a new chat.")
        return

    try:
        conversation = get_conversation(session_id)
    except Exception as e:
        st.error(f"Couldn't load conversation: {e}")
        return

    _render_header(conversation)
    st.markdown("---")
    _render_messages(session_id)
    _render_input(session_id)


def _render_header(conversation: dict) -> None:
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader(conversation["title"])
        st.caption(f"{conversation['provider']} / {conversation['model']}")
    with col2:
        if st.button("✏️ Edit"):
            st.session_state.editing_conversation = not st.session_state.editing_conversation

    if st.session_state.editing_conversation:
        _render_edit_form(conversation)


def _render_edit_form(conversation: dict) -> None:
    with st.form("edit_conversation_form"):
        new_title = st.text_input("Title", value=conversation["title"])

        mode_options = {"(none)": None}
        try:
            for mode in get_modes():
                mode_options[mode["title"]] = mode["mode_id"]
        except Exception:
            pass

        labels = list(mode_options.keys())
        current_label = next(
            (label for label, mid in mode_options.items() if mid == conversation.get("mode_id")),
            "(none)",
        )
        mode_label = st.selectbox("Mode", labels, index=labels.index(current_label))

        col1, col2 = st.columns(2)
        with col1:
            save = st.form_submit_button("Save", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if save:
            try:
                update_conversation(
                    conversation["session_id"],
                    title=new_title,
                    mode_id=mode_options[mode_label],
                )
                st.session_state.editing_conversation = False
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update conversation: {e}")

        if cancel:
            st.session_state.editing_conversation = False
            st.rerun()


def _render_messages(session_id: str) -> None:
    try:
        messages = get_messages(session_id)
    except Exception as e:
        st.error(f"Couldn't load messages: {e}")
        return

    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["message"])


def _render_input(session_id: str) -> None:
    prompt = st.chat_input("Type your message...")
    if not prompt:
        return

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # st.write_stream consumes a generator of string chunks, renders them
        # incrementally, and returns the full concatenated text once the
        # generator is exhausted. The backend interleaves "error"/"done"
        # events with "content" events on the same SSE stream, so we stash
        # those in `stream_meta` instead of yielding them as visible text.
        stream_meta = {"error": None, "latency_ms": None, "ttft_ms": None}

        def _text_chunks():
            try:
                for event in send_message_stream(session_id, prompt):
                    if "content" in event:
                        yield event["content"]
                    elif "error" in event:
                        stream_meta["error"] = event["error"]
                    elif event.get("done"):
                        stream_meta["latency_ms"] = event.get("latency_ms")
                        stream_meta["ttft_ms"] = event.get("ttft_ms")
            except Exception as e:
                stream_meta["error"] = str(e)
                yield f"⚠️ Error contacting backend: {e}"

        st.write_stream(_text_chunks())

        if stream_meta["error"]:
            st.error(stream_meta["error"])
        elif stream_meta["latency_ms"] is not None:
            st.caption(
                f"⏱️ {stream_meta['latency_ms']:.0f} ms total"
                f" · first token in {stream_meta['ttft_ms']:.0f} ms"
            )

    st.rerun()
