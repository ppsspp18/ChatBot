from uuid import uuid4
from datetime import datetime

from fastapi import HTTPException

from app.database.mongodb import (
    conversation_collection,
    message_collection
)


async def create_conversation(data):
    conversation = {
        "session_id": str(uuid4()),
        "title": data.title,
        "provider": data.provider,
        "model": data.model,
        "mode_id": data.mode_id,
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


async def edit_conversation(data):
    update_data = {
        "updated_at": datetime.utcnow()
    }

    if data.title is not None:
        update_data["title"] = data.title

    if data.provider is not None:
        update_data["provider"] = data.provider

    if data.model is not None:
        update_data["model"] = data.model

    if data.mode_id is not None:
        update_data["mode_id"] = data.mode_id

    result = await conversation_collection.update_one(
        {"session_id": data.session_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "message": "Conversation updated successfully"
    }


async def get_all_conversations():
    conversations = []

    async for conversation in conversation_collection.find().sort(
        "updated_at",
        -1
    ):
        conversation["_id"] = str(
            conversation["_id"]
        )

        conversations.append(
            conversation
        )

    return conversations


async def get_conversation(
    session_id: str
):
    conversation = await conversation_collection.find_one(
        {"session_id": session_id}
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    conversation["_id"] = str(
        conversation["_id"]
    )

    return conversation


async def cancel_conversation(
    session_id: str
):
    result = await conversation_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": "cancelled",
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "message": "Conversation cancelled successfully",
        "session_id": session_id
    }


async def activate_conversation(
    session_id: str
):
    result = await conversation_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": "active",
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "message": "Conversation activated successfully",
        "session_id": session_id
    }


async def delete_conversation(
    session_id: str
):
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

    return {
        "message": "Conversation deleted successfully"
    }