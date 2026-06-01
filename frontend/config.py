BACKEND_URL = "http://backend:8000"

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
    "groq":     "🟠 Groq",
    "google":   "🔵 Google",
    "deepseek": "🟣 DeepSeek",
}

STATUS_BADGE: dict[str, str] = {
    "active":    "🟢 Active",
    "cancelled": "🔴 Cancelled",
    "done":      "✅ Done",
}

STATUS_ICON: dict[str, str] = {
    "active":    "🟢",
    "cancelled": "🔴",
    "done":      "✅",
}

# Default session-state values used during initialisation
SESSION_DEFAULTS: dict = {
    "active_session_id": None,
    "messages":          [],
    "conversations":     [],
    "provider":          "groq",
    "model":             "llama-3.3-70b-versatile",
    "rename_mode":       False,
    "metrics_hours":     24,
    "show_ingest_form":  False,
}