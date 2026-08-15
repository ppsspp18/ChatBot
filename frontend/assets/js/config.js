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
    "gemma-4-31b-it",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite"
  ],
  groq: [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-safeguard-20b"
  ]
};

export const PROVIDERS = Object.keys(PROVIDERS_MODELS);