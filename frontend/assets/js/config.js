export const BACKEND_URL =
  window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : `${window.location.protocol}//${window.location.hostname}:8000`;

export const PROVIDERS_MODELS = {
  ollama: [
    "llama3.2:1b",
    "llama3.2:3b",
    "qwen3.5:0.8b",
    "deepseek-r1:1.5b",
    "gemma3:1b"
  ],
  google: [
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
    "gemini-3.1-flash-lite"
  ],
  deepseek: [
    "deepseek-v4-flash"
  ],
  groq: [
    "allam-2-7b",
    "groq/compound",
    "groq/compound-mini",
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-safeguard-20b",
    "qwen/qwen3-32b",
    "qwen/qwen3.6-27b",
    "whisper-large-v3",
    "whisper-large-v3-turbo"
  ],
  openrouter: [
    "openrouter/free",
    "meta-llama/llama-3.2-3b-instruct:free"
  ]
};

export const PROVIDERS = Object.keys(PROVIDERS_MODELS);