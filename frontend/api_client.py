import requests

BASE_URL = "http://backend:8000"

def create_chat(title, provider, model):

    response = requests.post(
        f"{BASE_URL}/chats",
        json={
            "title": title,
            "provider": provider,
            "model": model
        }
    )

    return response.json()


def get_chats():

    response = requests.get(
        f"{BASE_URL}/chats"
    )

    return response.json()


def delete_chat(chat_id):

    requests.delete(
        f"{BASE_URL}/chats/{chat_id}"
    )


def send_message(
    chat_id,
    provider,
    model,
    message
):

    response = requests.post(
        f"{BASE_URL}/chat/{chat_id}/message",
        json={
            "provider": provider,
            "model": model,
            "message": message
        }
    )

    return response.json()


def get_messages(chat_id):

    response = requests.get(
        f"{BASE_URL}/chat/{chat_id}/messages"
    )

    return response.json()