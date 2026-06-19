import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

REQUEST_TIMEOUT = 120
STREAM_TIMEOUT = 300

# Provider -> list of available models
PROVIDERS_MODELS = {
    "ollama": [
        "hermes3:3b",
        "gemma3:270m",
        "smollm:135m",
        "llama3.2:1b",
        "qwen3:1.7b",
        "gemma3:4b",
        "llama3.2:3b",
        "qwen2.5-coder:3b",
        "qwen3.5:0.8b",
        "qwen3:4b",
        "qwen3:0.6b",
        "deepseek-r1:1.5b",
        "gemma3:1b",
        "qwen2.5-coder:1.5b",
    ],
    "google": [
        "gemma-4-26b-a4b-it",
        "gemma-4-31b-it",
        "gemini-3.1-flash-lite",
    ],
    "deepseek": [
        "deepseek-v4-flash",
    ],
    "groq": [
        "openai/gpt-oss-20b",
    ],
}

PROVIDERS = list(PROVIDERS_MODELS.keys())