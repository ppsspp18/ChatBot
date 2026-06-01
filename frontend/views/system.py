import uuid

import pandas as pd
import streamlit as st

from api_client import _get, _post


def render_system() -> None:
    st.markdown("### 🛠️ System")

    if st.button("🔄  Refresh", key="sys_refresh"):
        st.rerun()

    st.divider()
    _render_health_checks()

    st.divider()
    _render_manual_ingest_form()

    st.divider()
    _render_conversations_table()


# ── Private helpers ────────────────────────────────────────────────────────────

def _render_health_checks() -> None:
    st.markdown("#### Health Checks")
    hc1, hc2 = st.columns(2)

    with hc1:
        health = _get("/health")
        if health:
            st.success(f"✅  Backend: **{health.get('status', '?')}**")
            st.caption(f"Ingestion queue size: {health.get('ingestion_queue_size', 0)}")
        else:
            st.error("❌  Backend unreachable")

    with hc2:
        ingest_h = _get("/ingest/health")
        if ingest_h:
            queue_sz = ingest_h.get("queue_size", 0)
            level    = "success" if queue_sz < 50 else "warning"
            getattr(st, level)(
                f"✅  Ingest pipeline: **{ingest_h.get('status', '?')}**"
            )
            st.caption(f"Queue depth: {queue_sz}")
        else:
            st.error("❌  Ingest endpoint unreachable")


def _render_manual_ingest_form() -> None:
    st.markdown("#### 📥 Manual Ingest Log")
    st.caption(
        "Submit a raw inference log directly to the ingestion pipeline "
        "(for testing / SDK simulation)."
    )

    with st.expander("Send inference log to POST /ingest"):
        active_sids = [
            c["session_id"]
            for c in st.session_state.conversations
            if c.get("status") == "active"
        ]
        if not active_sids:
            st.info("Create an active conversation first.")
            return

        i_sid      = st.selectbox("Session ID", active_sids, key="ingest_sid")
        i_provider = st.selectbox("Provider", ["groq", "google"], key="ingest_prov")
        i_model    = st.text_input("Model", value="llama-3.3-70b-versatile", key="ingest_model")

        i1, i2 = st.columns(2)
        with i1:
            i_lat    = st.number_input("Latency (ms)",      min_value=0.0, value=350.0, key="ingest_lat")
            i_prompt = st.number_input("Prompt tokens",     min_value=0,   value=50,    key="ingest_pt")
        with i2:
            i_ttft = st.number_input("TTFT (ms)",           min_value=0.0, value=120.0, key="ingest_ttft")
            i_comp = st.number_input("Completion tokens",   min_value=0,   value=80,    key="ingest_ct")

        i_status  = st.selectbox("Status", ["success", "error", "cancelled"], key="ingest_status")
        i_err_msg = ""
        if i_status == "error":
            i_err_msg = st.text_input("Error message", key="ingest_errmsg")

        i_input_preview  = st.text_input("Input preview",  value="Hello!",    key="ingest_inp")
        i_output_preview = st.text_input("Output preview", value="Hi there!", key="ingest_out")

        if st.button("📤  Submit Ingest Log", type="primary"):
            payload = {
                "session_id":        i_sid,
                "log_id":            str(uuid.uuid4()),
                "provider":          i_provider,
                "model":             i_model,
                "latency_ms":        i_lat,
                "ttft_ms":           i_ttft,
                "prompt_tokens":     i_prompt,
                "completion_tokens": i_comp,
                "total_tokens":      i_prompt + i_comp,
                "status":            i_status,
                "error_message":     i_err_msg or None,
                "pii_detected":      False,
                "entities":          [],
                "input_preview":     i_input_preview[:200],
                "output_preview":    i_output_preview[:200],
            }
            result = _post("/ingest", payload)
            if result:
                st.success(
                    f"✅  Accepted  ·  log_id: `{result.get('log_id')}`"
                    f"  ·  queue: {result.get('queue_size')}"
                )


def _render_conversations_table() -> None:
    st.markdown("#### 📋 All Conversations")
    if not st.session_state.conversations:
        st.caption("No conversations found.")
        return

    rows = [
        {
            "Title":      c["title"],
            "Status":     c.get("status", "—"),
            "Tokens":     c.get("total_tokens", 0),
            "Created":    str(c.get("created_at", ""))[:19],
            "Updated":    str(c.get("updated_at", ""))[:19],
            "Session ID": c["session_id"],
        }
        for c in st.session_state.conversations
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)