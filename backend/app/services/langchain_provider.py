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
    GROQ_API_KEY,
    GOOGLE_API_KEY,
    DEEPSEEK_API_KEY
)


class LLMFactory:

    @staticmethod
    def get_llm(provider: str, model: str):

        if provider == "groq":
            return ChatGroq(
                model=model,
                api_key=GROQ_API_KEY,
                temperature=0.7
            )

        elif provider == "google":
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=GOOGLE_API_KEY,
                temperature=0.7
            )

        elif provider == "deepseek":
            return ChatOpenAI(
                model=model,
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com",
                temperature=0.7
            )

        elif provider == "ollama":
            return ChatOllama(
                model=model,
                base_url="http://localhost:11434",
                temperature=0.7,
                keep_alive=0, 
                request_timeout=300
            )

        raise ValueError(f"Invalid provider: {provider}")


async def generate_stream(
    provider,
    model,
    messages
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

        if chunk.content:
            yield chunk.content


async def generate(
    provider: str,
    model: str,
    message: str,
    system_prompt: str | None = None
):
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

    response = await llm.ainvoke(
        lc_messages
    )

    return response.content


