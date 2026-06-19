import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

NON_STREAM_ENDPOINT = "/messages/ollama/{message}"
STREAM_ENDPOINT = "/messages/ollama/stream/{message}"

REQUEST_TIMEOUT = 120        # seconds, for the non-streaming call
STREAM_TIMEOUT = 300         # seconds, for the streaming call
