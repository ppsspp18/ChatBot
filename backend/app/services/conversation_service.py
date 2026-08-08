import uuid
from datetime import datetime
from typing import Any, List, Dict, Optional

from fastapi import HTTPException, status
from pymongo import ReturnDocument

from app.database.mongodb import (
    conversation_collection,
    message_collection,
    mode_collection,
)
from app.schemas.conversation_schema import (
    CreateConversationRequest,
    UpdateConversationRequest,
)


async def _find_conversation(
    conversation_id: str,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    return await conversation_collection.find_one(
        {"conversation_id": conversation_id, "user_id": user_id}
    )


async def _require_conversation(
    conversation_id: str,
    user_id: str,
) -> Dict[str, Any]:
    conversation = await _find_conversation(conversation_id, user_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    return doc


async def _validate_mode(mode_id: Optional[str], user_id: str) -> None:
    if not mode_id:
        return

    mode = await mode_collection.find_one(
        {"mode_id": mode_id, "user_id": user_id}
    )
    if mode is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mode not found or does not belong to this user",
        )


async def create_conversation(
    data: CreateConversationRequest,
    user_id: str,
) -> Dict[str, Any]:
    await _validate_mode(data.mode_id, user_id)

    now = datetime.utcnow()
    conversation = {
        "conversation_id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": data.title,
        "provider": data.provider,
        "model": data.model,
        "mode_id": data.mode_id,
        "total_tokens": 0,
        "created_at": now,
        "updated_at": now,
    }

    result = await conversation_collection.insert_one(conversation)
    conversation["_id"] = str(result.inserted_id)

    return conversation


async def get_conversation(
    conversation_id: str,
    user_id: str,
) -> Dict[str, Any]:
    conversation = await _require_conversation(conversation_id, user_id)
    return _serialize(conversation)


async def get_conversations(user_id: str) -> List[Dict[str, Any]]:
    conversations = (
        await conversation_collection
        .find({"user_id": user_id})
        .sort("updated_at", -1)
        .to_list(length=None)
    )

    return [_serialize(conv) for conv in conversations]


async def update_conversation(
    data: UpdateConversationRequest,
    user_id: str,
) -> Dict[str, Any]:
    await _require_conversation(data.conversation_id, user_id)

    result = await conversation_collection.find_one_and_update(
        {"conversation_id": data.conversation_id, "user_id": user_id},
        {"$set": {"title": data.title, "updated_at": datetime.utcnow()}},
        return_document=ReturnDocument.AFTER,
    )

    return _serialize(result)

async def delete_conversation(conversation_id: str, user_id: str) -> Dict[str, Any]:
    await _require_conversation(conversation_id, user_id)

    await conversation_collection.delete_one(
        {"conversation_id": conversation_id, "user_id": user_id}
    )
    await message_collection.delete_many({"conversation_id": conversation_id})

    return {"message": "Conversation deleted successfully"}