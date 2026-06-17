from uuid import uuid4
from datetime import datetime

from fastapi import HTTPException


from app.database.mongodb import (
    conversations_collection,
    messages_collection
)


async def create_conversation(data):
    """
    data: CreateConversationRequest (has .title attribute)
    Bug fix: previous code called with a raw str from the route.
    """
    conversation = {
        "session_id": str(uuid4()),
        "title": data.title,
        "status": "active",
        "total_tokens": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    await conversations_collection.insert_one(conversation)

    conversation["_id"] = str(conversation["_id"])

    return conversation


async def edit_conversation(data):
    result = await conversations_collection.update_one(
        {"session_id": data.session_id},
        {
            "$set": {
                "title": data.title,
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
        "message": "Conversation updated successfully"
    }


async def get_all_conversations():
    conversations = []

    async for conversation in conversations_collection.find().sort("updated_at", -1):
        conversation["_id"] = str(conversation["_id"])
        conversations.append(conversation)

    return conversations


async def get_conversation(session_id: str):
    conversation = await conversations_collection.find_one(
        {"session_id": session_id}
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    conversation["_id"] = str(conversation["_id"])

    return conversation


async def cancel_conversation(session_id: str):
    """
    Soft-cancel: sets status to 'cancelled', keeps all messages intact.
    The frontend can still resume the conversation (history preserved).
    """
    result = await conversations_collection.update_one(
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
        "session_id": str(session_id)
    }

async def activate_conversation(session_id: str):
    result = await conversations_collection.update_one(
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
        "session_id": str(session_id)
    }


async def delete_conversation(session_id: str):
    result = await conversations_collection.delete_one(
        {"session_id": session_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    await messages_collection.delete_many(
        {"session_id": str(session_id)}
    )

    return {
        "message": "Conversation deleted successfully"
    }

