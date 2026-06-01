import json

import requests
import streamlit as st

from config import BACKEND_URL

# ── HTTP primitives ────────────────────────────────────────────────────────────

def _get(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot reach backend. Is it running?")
    except Exception as exc:
        st.error(f"❌ GET {path} failed: {exc}")
    return None


def _post(path: str, body: dict | None = None):
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=body, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"❌ POST {path} failed: {exc}")
    return None


def _patch(path: str, params: dict | None = None):
    try:
        r = requests.patch(f"{BACKEND_URL}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"❌ PATCH {path} failed: {exc}")
    return None


def _delete(path: str, params: dict | None = None):
    try:
        r = requests.delete(f"{BACKEND_URL}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"❌ DELETE {path} failed: {exc}")
    return None


# ── Streaming ──────────────────────────────────────────────────────────────────

def _stream_tokens(session_id: str, message: str, provider: str, model: str):
    """Generator that yields text tokens from the SSE stream."""
    payload = {
        "session_id": session_id,
        "message":    message,
        "provider":   provider,
        "model":      model,
    }
    try:
        with requests.post(
            f"{BACKEND_URL}/messages/send/stream",
            json=payload,
            stream=True,
            timeout=120,
        ) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8")
                if not line.startswith("data: "):
                    continue
                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue

                if "token" in data:
                    yield data["token"]
                elif "error" in data:
                    yield f"\n\n❌ {data['error']}"
                    return
                elif data.get("done"):
                    return
    except Exception as exc:
        yield f"\n\n❌ Stream error: {exc}"


# ── Session-state data loaders ─────────────────────────────────────────────────

def load_conversations() -> None:
    """Fetch all conversations from the backend and store in session state."""
    data = _get("/conversations/all")
    st.session_state.conversations = data or []


def load_messages(session_id: str) -> None:
    """Fetch messages for *session_id* and store in session state."""
    data = _get("/messages/all", {"session_id": session_id})
    st.session_state.messages = data or []


def select_conversation(session_id: str) -> None:
    """Switch the active conversation and load its messages."""
    st.session_state.active_session_id = session_id
    st.session_state.rename_mode = False
    load_messages(session_id)