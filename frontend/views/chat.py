import streamlit as st

from api_client import (
    _patch,
    _post,
    _stream_tokens,
    load_conversations,
    load_messages,
)
from config import PROVIDER_BADGE, PROVIDERS_MODELS, STATUS_BADGE


def render_chat() -> None:
    if not st.session_state.active_session_id:
        st.info("👈  Select or create a conversation in the sidebar to get started.")
        st.stop()

    active_conv = next(
        (c for c in st.session_state.conversations
         if c["session_id"] == st.session_state.active_session_id),
        None,
    )

    # ── Header row ─────────────────────────────────────────────────────────────
    if active_conv:
        _render_conversation_header(active_conv)

    st.divider()

    # ── Provider / Model selectors ─────────────────────────────────────────────
    chosen_provider, chosen_model = _render_model_selector()

    st.divider()

    # ── Message history ────────────────────────────────────────────────────────
    _render_message_history()

    # ── Chat input ─────────────────────────────────────────────────────────────
    _render_chat_input(active_conv, chosen_provider, chosen_model)


# ── Private helpers ────────────────────────────────────────────────────────────

def _render_conversation_header(active_conv: dict) -> None:
    status  = active_conv.get("status", "active")
    h_col, a_col = st.columns([6, 2])

    with h_col:
        if st.session_state.rename_mode:
            r_col1, r_col2, r_col3 = st.columns([4, 1, 1])
            with r_col1:
                new_name = st.text_input(
                    "Rename",
                    value=active_conv["title"],
                    label_visibility="collapsed",
                )
            with r_col2:
                if st.button("✔", type="primary"):
                    _post(
                        "/conversations/edit",
                        {"session_id": st.session_state.active_session_id, "title": new_name},
                    )
                    st.session_state.rename_mode = False
                    load_conversations()
                    st.rerun()
            with r_col3:
                if st.button("✖"):
                    st.session_state.rename_mode = False
                    st.rerun()
        else:
            tokens = active_conv.get("total_tokens", 0)
            st.markdown(
                f"### {active_conv['title']}"
                f"&nbsp;&nbsp;`{STATUS_BADGE.get(status, status)}`"
                f"&nbsp;&nbsp;<sub>{tokens:,} tokens</sub>",
                unsafe_allow_html=True,
            )

    with a_col:
        ac1, ac2 = st.columns(2)
        with ac1:
            if st.button("✏️ Rename", use_container_width=True):
                st.session_state.rename_mode = True
                st.rerun()
        with ac2:
            if status == "active":
                if st.button("⏹️ Cancel", use_container_width=True):
                    _patch(
                        "/conversations/cancel",
                        {"session_id": st.session_state.active_session_id},
                    )
                    load_conversations()
                    st.rerun()


def _render_model_selector() -> tuple[str, str]:
    """Render provider + model dropdowns; return (chosen_provider, chosen_model)."""
    sel_col1, sel_col2, _ = st.columns([1, 2, 3])

    with sel_col1:
        providers = list(PROVIDERS_MODELS.keys())
        prov_idx  = (
            providers.index(st.session_state.provider)
            if st.session_state.provider in providers
            else 0
        )
        chosen_provider = st.selectbox(
            "Provider",
            options=providers,
            index=prov_idx,
            format_func=lambda p: PROVIDER_BADGE.get(p, p),
        )
        st.session_state.provider = chosen_provider

    with sel_col2:
        model_list = PROVIDERS_MODELS[chosen_provider]
        if st.session_state.model not in model_list:
            st.session_state.model = model_list[0]
        chosen_model = st.selectbox(
            "Model",
            options=model_list,
            index=model_list.index(st.session_state.model),
        )
        st.session_state.model = chosen_model

    return chosen_provider, chosen_model


def _render_message_history() -> None:
    for msg in st.session_state.messages:
        role         = msg.get("role", "user")
        content      = msg.get("message", "")
        msg_provider = msg.get("provider", "")
        msg_model    = msg.get("model", "")

        if role == "system":
            continue

        avatar = "🧑" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.markdown(content)
            if msg_provider and msg_model:
                badge = PROVIDER_BADGE.get(msg_provider, msg_provider)
                st.caption(f"{badge}  ·  `{msg_model}`")


def _render_chat_input(
    active_conv: dict | None,
    chosen_provider: str,
    chosen_model: str,
) -> None:
    is_cancelled = active_conv.get("status") == "cancelled" if active_conv else False

    if is_cancelled:
        st.warning("⚠️  This conversation is cancelled — no new messages can be sent.")
        return

    user_input = st.chat_input("Type your message…")
    if not user_input:
        return

    provider_badge = PROVIDER_BADGE.get(chosen_provider, chosen_provider)

    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
        st.caption(f"{provider_badge}  ·  `{chosen_model}`")

    with st.chat_message("assistant", avatar="🤖"):
        st.write_stream(
            _stream_tokens(
                session_id=st.session_state.active_session_id,
                message=user_input,
                provider=chosen_provider,
                model=chosen_model,
            )
        )
        st.caption(f"{provider_badge}  ·  `{chosen_model}`")

    load_messages(st.session_state.active_session_id)
    load_conversations()
    st.rerun()