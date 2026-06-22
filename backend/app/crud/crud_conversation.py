from datetime import datetime
from uuid import uuid4
from typing import Optional

from fastapi import HTTPException

from app.database.mongodb import (
    conversation_collection
)

from app.crud.crud_mode import (
    validate_mode
)


# Validation
async def validate_conversation(
    session_id: str,
    allow_cancelled: bool = False
):
    conversation = await conversation_collection.find_one(
        {"session_id": session_id}
    )

    if not conversation:
        raise ValueError(
            "Conversation not found"
        )

    if (
        not allow_cancelled
        and conversation["status"] == "cancelled"
    ):
        raise ValueError(
            "Conversation is cancelled"
        )
    return conversation


# Create
async def create_conversation_db(
    title: str,
    provider: str,
    model: str,
    mode_id: Optional[str] = None
):
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

    conversation["_id"] = str(
        result.inserted_id
    )

    return conversation


# Read
async def get_conversation_by_session_id(
    session_id: str
):
    return await conversation_collection.find_one(
        {"session_id": session_id}
    )


async def get_all_conversations_db():
    conversations = []

    async for conversation in (
        conversation_collection
        .find()
        .sort("updated_at", -1)
    ):
        conversation["_id"] = str(
            conversation["_id"]
        )

        conversations.append(
            conversation
        )

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
    update_data = {
        "updated_at": datetime.utcnow()
    }

    if title is not None:
        update_data["title"] = title

    if provider is not None:
        update_data["provider"] = provider

    if model is not None:
        update_data["model"] = model

    if mode_id is not None:
        update_data["mode_id"] = mode_id

    update_query = {
        "$set": update_data
    }

    if total_tokens:
        update_query["$inc"] = {
            "total_tokens": total_tokens
        }

    result = await conversation_collection.update_one(
        {"session_id": session_id},
        update_query
    )

    return result


async def update_conversation_status(
    session_id: str,
    status: str
):
    return await conversation_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }
        }
    )


# Delete
async def delete_conversation_db(
    session_id: str
):
    return await conversation_collection.delete_one(
        {"session_id": session_id}
    )


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