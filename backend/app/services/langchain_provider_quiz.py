import json

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from app.config.settings import GROQ_API_KEY


QUIZ_MODEL = "llama-3.3-70b-versatile"


def extract_text(content):
    """
    Extract text from LangChain response content.
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

    return str(content)


async def generate_quiz(prompt: str) -> dict:
    """
    Generate a quiz using the Groq LLM.

    Args:
        prompt: Complete prompt instructing the LLM to generate the quiz.

    Returns:
        Parsed JSON response as a Python dictionary.

    Raises:
        ValueError:
            If the API key is missing or the model returns invalid JSON.
    """

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured.")

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=QUIZ_MODEL,
        temperature=0.7,
    )

    response = await llm.ainvoke(
        [
            HumanMessage(content=prompt)
        ]
    )

    text = extract_text(response.content).strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()

        if lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model returned invalid JSON.\n\n{text}"
        ) from exc