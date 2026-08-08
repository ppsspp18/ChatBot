const PROD_BACKEND_URL = "https://chatbot-j3lf.onrender.com";

function resolveBackendUrl() {
  const hostname = window.location.hostname;

  const isLocalhost =
    hostname === "localhost" ||
    hostname === "127.0.0.1";

  if (isLocalhost) {
    return "http://localhost:8000";
  }

  return PROD_BACKEND_URL;
}

export const BACKEND_URL = resolveBackendUrl();

export const PROVIDERS_MODELS = {
  google: [
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it"
  ],
  groq: [
    "groq/compound",
    "groq/compound-mini",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "qwen/qwen3.6-27b"
  ],
  openrouter: [
    "openrouter/free"
  ]
};

export const PROVIDERS = Object.keys(PROVIDERS_MODELS);