import requests
from config import BACKEND_URL

def create_conversation(title: str = "NEW CONVERSATION") -> dict:
    res = requests.post(f"{BACKEND_URL}/conversations/add", json={"title": title})
    res.raise_for_status()
    return res.json()

def get_all_conversations() -> list:
    res = requests.get(f"{BACKEND_URL}/conversations/all")
    res.raise_for_status()
    return res.json()

def get_conversation(session_id: str) -> dict:
    res = requests.get(f"{BACKEND_URL}/conversations/get", params={"session_id": session_id})
    res.raise_for_status()
    return res.json()

def edit_conversation(session_id: str, title: str) -> dict:
    res = requests.post(f"{BACKEND_URL}/conversations/edit", json={"session_id": session_id, "title": title})
    res.raise_for_status()
    return res.json()

def delete_conversation(session_id: str) -> dict:
    res = requests.delete(f"{BACKEND_URL}/conversations/delete", params={"session_id": session_id})
    res.raise_for_status()
    return res.json()

def get_messages(session_id: str) -> list:
    res = requests.get(f"{BACKEND_URL}/messages/all", params={"session_id": session_id})
    res.raise_for_status()
    return res.json()

# --- NEW: Non-Streaming Route ---
def send_message(session_id: str, message: str, provider: str, model: str) -> dict:
    res = requests.post(
        f"{BACKEND_URL}/messages/send",
        json={
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "message": message
        },
        timeout=60
    )
    res.raise_for_status()
    return res.json()

# --- Streaming Route ---
def send_message_stream(session_id: str, message: str, provider: str, model: str):
    return requests.post(
        f"{BACKEND_URL}/messages/send/stream",
        json={
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "message": message
        },
        stream=True,
        timeout=60
    )