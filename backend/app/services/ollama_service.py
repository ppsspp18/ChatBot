from datetime import datetime
from ollama import AsyncClient

from backend.app.schemas.message_schema import MessageRequest, MessageSchema

# Replace these with your actual repository functions
from app.repositories.messages import (
    get_messages_by_session_id,
    get_next_sequence,
    create_message,
)

OLLAMA_HOST = "http://localhost:11434"


async def get_ollama_messages(data: MessageRequest):
    """
    1. Store user message
    2. Load conversation history
    3. Send history to Ollama
    4. Store assistant response
    5. Return response
    """

    # Save user message
    user_message = MessageSchema(
        session_id=data.session_id,
        role="user",
        message=data.message,
        provider=data.provider,
        model=data.model,
        sequence=await get_next_sequence(data.session_id),
        timestamp=datetime.utcnow(),
    )

    await create_message(user_message)

    # Fetch complete chat history
    history = await get_messages_by_session_id(data.session_id)

    ollama_messages = [
        {
            "role": msg.role,
            "content": msg.message,
        }
        for msg in history
    ]

    client = AsyncClient(host=OLLAMA_HOST)

    response = await client.chat(
        model=data.model,
        messages=ollama_messages,
    )

    assistant_text = response["message"]["content"]

    # Save assistant message
    assistant_message = MessageSchema(
        session_id=data.session_id,
        role="assistant",
        message=assistant_text,
        provider=data.provider,
        model=data.model,
        sequence=await get_next_sequence(data.session_id),
        timestamp=datetime.utcnow(),
    )

    await create_message(assistant_message)

    return {
        "session_id": data.session_id,
        "provider": data.provider,
        "model": data.model,
        "response": assistant_text,
    }