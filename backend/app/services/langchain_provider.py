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
    DEEPSEEK_API_KEY,
    OPENROUTER_API_KEY
)


def extract_text(content):
    """
    Extract text content from various response formats.
    
    Handles:
    - String: returns as-is
    - List of strings: joins them
    - List of dicts: extracts 'text' fields
    - List of objects: extracts 'text' attributes
    - None: returns empty string
    - Other types: converts to string
    """
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

    # Fallback for any other type
    return str(content)


class LLMFactory:

    @staticmethod
    def get_llm(provider: str, model: str):
        """
        Factory method to create LLM instances based on provider.
        
        Supported providers:
        - groq
        - google
        - deepseek
        - openrouter
        - ollama
        """
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

        elif provider == "openrouter":
            return ChatOpenAI(
                model=model,
                api_key=OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.7
            )

        elif provider == "ollama":
            return ChatOllama(
                model=model,
                base_url="http://host.docker.internal:11434",
                temperature=0.7,
                keep_alive=0,
                request_timeout=400
            )

        raise ValueError(f"Invalid provider: {provider}")


async def generate_stream(
    provider: str,
    model: str,
    messages: list[dict]
):
    """
    Generate a streaming response from the LLM.
    
    Args:
        provider: LLM provider (groq, google, deepseek, openrouter, ollama)
        model: Model name/identifier
        messages: List of message dicts with 'role' and 'content' keys
    
    Yields:
        Text chunks as strings
    """
    llm = LLMFactory.get_llm(
        provider=provider,
        model=model
    )

    # Convert messages to LangChain format
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

    # Stream responses with proper text extraction
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
    """
    Generate a complete (non-streaming) response from the LLM.
    
    Args:
        provider: LLM provider (groq, google, deepseek, openrouter, ollama)
        model: Model name/identifier
        message: User message
        system_prompt: Optional system prompt
    
    Returns:
        Complete response as string
    """
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
    
    # Extract text from response content
    return extract_text(response.content)