import json
from typing import Any, Dict, Iterator, List, Optional

import requests

from config import BACKEND_URL, REQUEST_TIMEOUT, STREAM_TIMEOUT

# Conversations

def create_conversation(
    title: str,
    provider: str,
    model: str,
    mode_id: Optional[str] = None,
) -> Dict[str, Any]:
    resp = requests.post(
        f"{BACKEND_URL}/conversations/",
        json={"title": title, "provider": provider, "model": model, "mode_id": mode_id},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def update_conversation(session_id: str, **fields: Any) -> Dict[str, Any]:
    """fields may include title, provider, model, mode_id. None values are dropped."""
    payload = {"session_id": session_id}
    payload.update({k: v for k, v in fields.items() if v is not None})
    resp = requests.patch(f"{BACKEND_URL}/conversations/", json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_conversations() -> List[Dict[str, Any]]:
    resp = requests.get(f"{BACKEND_URL}/conversations/", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_conversation(session_id: str) -> Dict[str, Any]:
    resp = requests.get(f"{BACKEND_URL}/conversations/{session_id}", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def delete_conversation(session_id: str) -> None:
    resp = requests.delete(f"{BACKEND_URL}/conversations/{session_id}", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()


def cancel_conversation(session_id: str) -> Dict[str, Any]:
    resp = requests.patch(f"{BACKEND_URL}/conversations/cancel/{session_id}", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def activate_conversation(session_id: str) -> Dict[str, Any]:
    resp = requests.patch(f"{BACKEND_URL}/conversations/activate/{session_id}", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# Modes

def create_mode(title: str, description: str, system_prompt: str) -> Dict[str, Any]:
    resp = requests.post(
        f"{BACKEND_URL}/modes/",
        json={"title": title, "description": description, "system_prompt": system_prompt},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_modes() -> List[Dict[str, Any]]:
    resp = requests.get(f"{BACKEND_URL}/modes/", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_mode(mode_id: str) -> Dict[str, Any]:
    resp = requests.get(f"{BACKEND_URL}/modes/{mode_id}", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def edit_mode(mode_id: str, title: str, description: str, system_prompt: str) -> Dict[str, Any]:
    resp = requests.patch(
        f"{BACKEND_URL}/modes/{mode_id}",
        json={"title": title, "description": description, "system_prompt": system_prompt},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def delete_mode(mode_id: str) -> None:
    resp = requests.delete(f"{BACKEND_URL}/modes/{mode_id}", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()


# Messages

def get_messages(session_id: str) -> List[Dict[str, Any]]:
    resp = requests.get(f"{BACKEND_URL}/messages/{session_id}", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def send_message_stream(session_id: str, message: str) -> Iterator[Dict[str, Any]]:
    """
    Streams a reply from the backend's SSE endpoint (POST /messages/).

    The backend returns `text/event-stream`, with each event formatted as
    `data: {...}\\n\\n`. This yields one parsed dict per event, e.g.:

        {"content": "..."}                                  -- a text chunk
        {"error": "..."}                                     -- a server-side error
        {"done": True, "latency_ms": ..., "ttft_ms": ...}     -- stream finished
    """
    with requests.post(
        f"{BACKEND_URL}/messages/",
        json={"session_id": session_id, "message": message},
        timeout=STREAM_TIMEOUT,
        stream=True,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            data_str = line[len("data:"):].strip()
            if not data_str:
                continue
            try:
                yield json.loads(data_str)
            except json.JSONDecodeError:
                continue
