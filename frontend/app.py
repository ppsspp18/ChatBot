import streamlit as st

from api_client import (
    _delete,
    _post,
    load_conversations,
    select_conversation,
)
from config import PROVIDER_BADGE, SESSION_DEFAULTS, STATUS_ICON
from views import render_chat, render_metrics, render_system

# ── 1. Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="LLM Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. Global CSS ──────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* Tighten sidebar button spacing */
    [data-testid="stSidebar"] .stButton > button {
        text-align: left;
        font-size: 0.85rem;
    }
    /* Make chat messages slightly wider */
    [data-testid="stChatMessage"] {
        max-width: 100% !important;
    }
    /* Metric card value size */
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── 3. Session-state initialisation ───────────────────────────────────────────

for _key, _default in SESSION_DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ── 4. Load data on every render ───────────────────────────────────────────────

load_conversations()

# ── 5. Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🤖 LLM Chat")
    st.divider()

    # ── New conversation ───────────────────────────────────────────────────────
    with st.expander("➕  New Conversation"):
        new_title = st.text_input(
            "Title", placeholder="Conversation title…", key="new_conv_title"
        )
        if st.button("Create", type="primary", use_container_width=True):
            if new_title.strip():
                res = _post("/conversations/add", {"title": new_title.strip()})
                if res:
                    select_conversation(res["session_id"])
                    st.rerun()
            else:
                st.warning("Please enter a title.")

    st.divider()
    st.markdown("**Conversations**")

    if not st.session_state.conversations:
        st.caption("No conversations yet.")

    for conv in st.session_state.conversations:
        sid       = conv["session_id"]
        status    = conv.get("status", "active")
        icon      = STATUS_ICON.get(status, "⚪")
        is_active = sid == st.session_state.active_session_id

        col_btn, col_del = st.columns([5, 1])
        with col_btn:
            if st.button(
                f"{icon} {conv['title']}",
                key=f"conv_{sid}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                select_conversation(sid)
                st.rerun()
        with col_del:
            if st.button("🗑", key=f"del_{sid}", help="Delete conversation"):
                _delete("/conversations/delete", {"session_id": sid})
                if st.session_state.active_session_id == sid:
                    st.session_state.active_session_id = None
                    st.session_state.messages = []
                load_conversations()
                st.rerun()

# ── 6. Main tabs ───────────────────────────────────────────────────────────────

tab_chat, tab_metrics, tab_system = st.tabs(
    ["💬  Chat", "📊  Metrics", "🛠️  System"]
)

with tab_chat:
    render_chat()

with tab_metrics:
    render_metrics()

with tab_system:
    render_system()