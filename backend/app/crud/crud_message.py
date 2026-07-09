from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database.mongodb import message_collection


async def insert_message(
    session_id: str,
    role: str,
    message: str,
    provider: str,
    model: str,
    sequence: int,
    inference_log_id: Optional[str] = None
) -> str:
    doc = {
        "session_id": session_id,
        "role": role,
        "message": message,
        "provider": provider,
        "model": model,
        "sequence": sequence,
        "timestamp": datetime.utcnow(),
        "inference_log_id": inference_log_id
    }

    result = await message_collection.insert_one(doc)
    return str(result.inserted_id)


async def get_messages_by_session_id(
    session_id: str
) -> List[Dict[str, Any]]:
    messages = []

    async for message in message_collection.find(
        {"session_id": session_id}
    ).sort("sequence", 1):
        message["_id"] = str(message["_id"])
        if message.get("inference_log_id"):
            message["inference_log_id"] = str(message["inference_log_id"])
        messages.append(message)

    return messages


async def delete_messages_by_session_id(
    session_id: str
):
    return await message_collection.delete_many(
        {"session_id": session_id}
    )