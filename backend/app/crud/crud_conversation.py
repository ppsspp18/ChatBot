from datetime import datetime
from uuid import uuid4
from typing import Optional, List, Dict, Any

from fastapi import HTTPException

from app.database.mongodb import (
    conversation_collection,
    message_collection
)

from app.crud.crud_mode import (
    validate_mode
)


# Validation
async def validate_conversation(
    session_id: str,
    allow_cancelled: bool = False
) -> Dict[str, Any]:
    conversation = await conversation_collection.find_one(
        {"session_id": session_id}
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    if (
        not allow_cancelled
        and conversation["status"] == "cancelled"
    ):
        raise HTTPException(
            status_code=400,
            detail="Conversation is cancelled"
        )

    conversation["_id"] = str(conversation["_id"])
    return conversation


# Create
async def create_conversation(
    title: str,
    provider: str,
    model: str,
    mode_id: Optional[str] = None
) -> Dict[str, Any]:
    if mode_id:
        await validate_mode(mode_id)

    conversation = {
        "session_id": str(uuid4()),
        "title": title,
        "provider": provider,
        "model": model,
        "mode_id": mode_id,
        "status": "active",
        "total_tokens": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await conversation_collection.insert_one(
        conversation
    )

    conversation["_id"] = str(result.inserted_id)
    return conversation


# Read
async def get_conversation(
    session_id: str
) -> Dict[str, Any]:
    return await validate_conversation(session_id)


async def get_all_conversations() -> List[Dict[str, Any]]:
    conversations = []

    async for conversation in (
        conversation_collection
        .find()
        .sort("updated_at", -1)
    ):
        conversation["_id"] = str(conversation["_id"])
        conversations.append(conversation)

    return conversations


# Update
async def update_conversation(
    session_id: str,
    title: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    mode_id: Optional[str] = None,
    total_tokens: int = 0
):
    await validate_conversation(session_id, allow_cancelled=True)

    update_data = {"updated_at": datetime.utcnow()}

    if title is not None:
        update_data["title"] = title
    if provider is not None:
        update_data["provider"] = provider
    if model is not None:
        update_data["model"] = model
    if mode_id is not None:
        update_data["mode_id"] = mode_id

    update_query = {"$set": update_data}

    if total_tokens:
        update_query["$inc"] = {"total_tokens": total_tokens}

    await conversation_collection.update_one(
        {"session_id": session_id},
        update_query
    )


async def update_conversation_status(
    session_id: str,
    status: str
) -> Dict[str, str]:
    await validate_conversation(session_id, allow_cancelled=True)

    await conversation_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }
        }
    )

    status_label = "cancelled" if status == "cancelled" else "activated"
    return {
        "message": f"Conversation {status_label} successfully",
        "session_id": session_id
    }


# Delete
async def delete_conversation(
    session_id: str
) -> Dict[str, str]:
    await validate_conversation(session_id, allow_cancelled=True)

    result = await conversation_collection.delete_one(
        {"session_id": session_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    await message_collection.delete_many(
        {"session_id": session_id}
    )

    return {"message": "Conversation deleted successfully"}


# Update many
async def remove_mode_from_conversations(
    mode_id: str
):
    return await conversation_collection.update_many(
        {"mode_id": mode_id},
        {
            "$set": {
                "mode_id": None,
                "updated_at": datetime.utcnow()
            }
        }
    )