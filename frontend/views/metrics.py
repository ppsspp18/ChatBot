import pandas as pd
import streamlit as st

from api_client import _get


def render_metrics() -> None:
    st.markdown("### 📊 Inference Metrics")

    hours = _render_window_selector()
    st.divider()

    _render_overview(hours)
    st.divider()

    row1_left, row1_right = st.columns(2)
    with row1_left:
        _render_latency(hours)
    with row1_right:
        _render_errors(hours)

    st.divider()

    row2_left, row2_right = st.columns(2)
    with row2_left:
        _render_tokens(hours)
    with row2_right:
        _render_throughput(hours)


# ── Private helpers ────────────────────────────────────────────────────────────

def _render_window_selector() -> int:
    """Render the lookback-window slider + refresh button; return chosen hours."""
    m_col1, m_col2 = st.columns([2, 1])

    with m_col1:
        hours = st.slider(
            "Lookback window (hours)",
            min_value=1,
            max_value=168,
            value=st.session_state.metrics_hours,
            step=1,
            key="metrics_hours_slider",
        )
        st.session_state.metrics_hours = hours

    with m_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄  Refresh", type="primary", use_container_width=True):
            st.rerun()

    return hours


def _render_overview(hours: int) -> None:
    st.markdown("#### Overview")
    overview = _get("/metrics/overview", {"hours": hours})
    if not overview:
        st.info("No data yet for the selected window.")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Calls",  f"{overview.get('total_calls', 0):,}")
    c2.metric("Total Tokens", f"{overview.get('total_tokens', 0):,}")
    c3.metric("Errors",       f"{overview.get('error_count', 0):,}")
    c4.metric("Avg Latency",  f"{overview.get('avg_latency_ms', 0):.0f} ms")
    c5.metric("Error Rate",   f"{overview.get('error_rate', 0):.1f}%")


def _render_latency(hours: int) -> None:
    st.markdown("#### ⏱️ Latency")
    latency = _get("/metrics/latency", {"hours": hours})

    if not latency or latency.get("sample_count", 0) == 0:
        st.caption("No latency data yet.")
        return

    lc1, lc2, lc3 = st.columns(3)
    lc1.metric("p50", f"{latency['p50_ms']:.0f} ms")
    lc2.metric("p95", f"{latency['p95_ms']:.0f} ms")
    lc3.metric("p99", f"{latency['p99_ms']:.0f} ms")

    ts = latency.get("time_series", [])
    if ts:
        df_lat = pd.DataFrame(ts)[["timestamp", "avg_latency_ms"]].set_index("timestamp")
        st.line_chart(df_lat, use_container_width=True)


def _render_errors(hours: int) -> None:
    st.markdown("#### ❌ Errors")
    errors = _get("/metrics/errors", {"hours": hours})

    if not errors:
        st.caption("No error data.")
        return

    by_prov = errors.get("by_provider", [])
    ts_err  = errors.get("time_series", [])

    if by_prov:
        df_ep = pd.DataFrame(by_prov).set_index("provider")
        st.bar_chart(df_ep["count"], use_container_width=True)
    else:
        st.success("✅  No errors in this window.")

    if ts_err:
        df_ets = (
            pd.DataFrame(ts_err)[["timestamp", "error_rate"]]
            .set_index("timestamp")
        )
        st.area_chart(df_ets, use_container_width=True)


def _render_tokens(hours: int) -> None:
    st.markdown("#### 🔤 Token Usage")
    tokens = _get("/metrics/tokens", {"hours": hours})

    if not tokens:
        st.caption("No token data yet.")
        return

    by_prov_tok  = tokens.get("by_provider", [])
    by_model_tok = tokens.get("by_model", [])

    if by_prov_tok:
        df_tp = (
            pd.DataFrame(by_prov_tok)
            [["provider", "prompt_tokens", "completion_tokens"]]
            .set_index("provider")
        )
        st.bar_chart(df_tp, use_container_width=True)

    if by_model_tok:
        st.markdown("**By model**")
        df_tm = pd.DataFrame(by_model_tok)[
            ["provider", "model", "total_tokens", "call_count"]
        ]
        df_tm.columns = ["Provider", "Model", "Total Tokens", "Calls"]
        st.dataframe(df_tm, use_container_width=True, hide_index=True)


def _render_throughput(hours: int) -> None:
    st.markdown("#### 🚀 Throughput")
    throughput = _get("/metrics/throughput", {"hours": hours})

    if not throughput:
        st.caption("No throughput data yet.")
        return

    tc1, tc2 = st.columns(2)
    tc1.metric("Avg RPM",        f"{throughput.get('avg_rpm', 0):.2f}")
    tc2.metric("Total Requests", f"{throughput.get('total_requests', 0):,}")

    per_hour = throughput.get("per_hour", [])
    if per_hour:
        df_ph = (
            pd.DataFrame(per_hour)[["timestamp", "requests"]]
            .set_index("timestamp")
        )
        st.line_chart(df_ph, use_container_width=True)