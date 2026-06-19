import json
import urllib.parse
from typing import Iterator

import requests

from config import (
    BACKEND_URL,
    NON_STREAM_ENDPOINT,
    STREAM_ENDPOINT,
    REQUEST_TIMEOUT,
    STREAM_TIMEOUT,
)


def _build_url(template: str, message: str) -> str:
    # message goes into the URL path, so it must be URL-encoded
    # (handles spaces, punctuation, etc.)
    encoded = urllib.parse.quote(message, safe="")
    return f"{BACKEND_URL}{template.format(message=encoded)}"


def get_response(message: str) -> str:
    """
    Calls GET /ollama/{message} and returns the full response text.
    get_message_simple() in the backend returns a plain string, which
    FastAPI serializes as a JSON string -> resp.json() gives back a str.
    """
    url = _build_url(NON_STREAM_ENDPOINT, message)
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    try:
        data = resp.json()
        return data if isinstance(data, str) else str(data)
    except ValueError:
        return resp.text


def get_response_stream(message: str) -> Iterator[str]:
    """
    Calls GET /ollama/stream/{message} (SSE) and yields text chunks
    as they arrive. Backend sends lines like:
        data: {"content": "..."}
    """
    url = _build_url(STREAM_ENDPOINT, message)

    with requests.get(url, stream=True, timeout=STREAM_TIMEOUT) as resp:
        resp.raise_for_status()
        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            if raw_line.startswith("data:"):
                payload = raw_line[len("data:"):].strip()
                try:
                    data = json.loads(payload)
                    chunk = data.get("content", "")
                except json.JSONDecodeError:
                    chunk = payload
                if chunk:
                    yield chunk
