import json
import random

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from app.config.settings import GROQ_API_KEY, GOOGLE_API_KEY, OPENROUTER_API_KEY


# Provider -> list of available models
PROVIDER_MODELS = {
    "google": [
        "gemma-4-26b-a4b-it",
        "gemma-4-31b-it",
    ],
    "groq": [
        "groq/compound",
        "groq/compound-mini",
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3-32b",
        "qwen/qwen3.6-27b",
    ],
    "openrouter": [
        "openrouter/free",
    ],
}


MAX_RETRIES = 5


def _pick_random_provider_model():
    provider = random.choice(list(PROVIDER_MODELS.keys()))
    model = random.choice(PROVIDER_MODELS[provider])
    return provider, model


def _create_llm(provider: str, model: str):
    if provider == "google":
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not configured")
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7,
        )

    if provider == "groq":
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured")
        return ChatGroq(
            api_key=GROQ_API_KEY,
            model=model,
            temperature=0.7,
        )

    if provider == "openrouter":
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not configured")
        return ChatOpenAI(
            model=model,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7,
        )

    raise ValueError(f"Unknown provider: {provider}")


def extract_text(content):
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(text)
            elif hasattr(item, "text"):
                if item.text:
                    parts.append(item.text)
        return "".join(parts)

    return str(content)


async def generate_quiz(prompt: str) -> dict:
    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        provider, model = _pick_random_provider_model()

        try:
            llm = _create_llm(provider, model)

            response = await llm.ainvoke([HumanMessage(content=prompt)])

            text = extract_text(response.content).strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()

            return json.loads(text)

        except Exception as exc:
            last_exception = exc
            continue

    raise RuntimeError(
        f"All {MAX_RETRIES} attempts failed. Last error: {last_exception}"
    )