import json

import requests
import streamlit as st

from config import BACKEND_URL


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

def _stream_tokens(session_id: str, message: str, provider: str, model: str):
    payload = {
        "session_id": session_id,
        "message":    message,
        "provider":   provider,
        "model":      model,
    }

    response_container = st.empty()
    full_response = ""
    try:
        with requests.post(
            f"{BACKEND_URL}/messages/send/stream",
            json=payload,
            stream=True,
            timeout=120,
        ) as response:  
            for chunk in response.iter_content(
                    chunk_size=1,
                    decode_unicode=True
                ):

                    if chunk:

                        full_response += chunk

                        response_container.markdown(full_response)
    
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")


def load_conversations() -> None:
    data = _get("/conversations/all")
    st.session_state.conversations = data or []


def load_messages(session_id: str) -> None:
    data = _get("/messages/all", {"session_id": session_id})
    st.session_state.messages = data or []


def select_conversation(session_id: str) -> None:
    st.session_state.active_session_id = session_id
    st.session_state.rename_mode = False
    load_messages(session_id)