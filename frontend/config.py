import os

# Point this to your backend service name in docker-compose
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

PROVIDERS_MODELS: dict[str, list[str]] = {
    "groq": [
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "qwen/qwen3-32b",
    ],
    "google": [
        "gemma-4-31b-it",
        "gemini-3.1-flash-lite",
    ],
    "deepseek": [
        "deepseek-v4-flash",
    ],
}

PROVIDER_BADGE: dict[str, str] = {
    "groq": "🟠 Groq",
    "google": "🔵 Google",
    "deepseek": "🟣 DeepSeek",
}