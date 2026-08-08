from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

from app.config.settings import (
    APP_ENV,
    GROQ_API_KEY,
    GOOGLE_API_KEY,
    DEEPSEEK_API_KEY,
    OPENROUTER_API_KEY
)


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


class LLMFactory:

    @staticmethod
    def get_llm(provider: str, model: str):
        provider = provider.lower().strip()

        if provider == "groq":
            if not GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not configured.")
            return ChatGroq(
                model=model,
                api_key=GROQ_API_KEY,
                temperature=0.7
            )

        elif provider == "google":
            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is not configured.")
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=GOOGLE_API_KEY,
                temperature=0.7
            )

        elif provider == "deepseek":
            if not DEEPSEEK_API_KEY:
                raise ValueError("DEEPSEEK_API_KEY is not configured.")
            return ChatOpenAI(
                model=model,
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com",
                temperature=0.7
            )

        elif provider == "openrouter":
            if not OPENROUTER_API_KEY:
                raise ValueError("OPENROUTER_API_KEY is not configured.")
            return ChatOpenAI(
                model=model,
                api_key=OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.7
            )


        raise ValueError(f"Invalid provider: {provider}")


async def generate_stream(
    provider: str,
    model: str,
    messages: list[dict]
):
    
    llm = LLMFactory.get_llm(
        provider=provider,
        model=model
    )

    lc_messages = []

    for msg in messages:
        if msg["role"] == "system":
            lc_messages.append(
                SystemMessage(content=msg["content"])
            )
        elif msg["role"] == "user":
            lc_messages.append(
                HumanMessage(content=msg["content"])
            )
        elif msg["role"] == "assistant":
            lc_messages.append(
                AIMessage(content=msg["content"])
            )

    async for chunk in llm.astream(lc_messages):
        text = extract_text(chunk.content)
        if text:
            yield text


async def generate(
    provider: str,
    model: str,
    message: str,
    system_prompt: str | None = None
) -> str:
    
    llm = LLMFactory.get_llm(
        provider=provider,
        model=model
    )

    lc_messages = []

    if system_prompt:
        lc_messages.append(
            SystemMessage(content=system_prompt)
        )

    lc_messages.append(
        HumanMessage(content=message)
    )

    response = await llm.ainvoke(lc_messages)
    return extract_text(response.content)