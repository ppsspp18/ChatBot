import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.database.mongodb import (
    conversation_collection,
    mode_collection,
)
from app.schemas.mode_schema import ModeRequest


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    return doc


async def _require_mode(mode_id: str, user_id: str) -> Dict[str, Any]:
    mode = await mode_collection.find_one({"mode_id": mode_id, "user_id": user_id})
    if mode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mode not found",
        )
    return mode


async def _validate_mode_title(
    title: str,
    user_id: str,
    exclude_mode_id: Optional[str] = None,
) -> None:
    query: Dict[str, Any] = {"title": title, "user_id": user_id}

    if exclude_mode_id:
        query["mode_id"] = {"$ne": exclude_mode_id}

    existing = await mode_collection.find_one(query)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mode title already exists",
        )


async def create_mode(data: ModeRequest, user_id: str) -> Dict[str, Any]:
    await _validate_mode_title(data.title, user_id)

    mode = {
        "mode_id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": data.title,
        "description": data.description,
        "system_prompt": data.system_prompt,
        "updated_at": datetime.utcnow(),
    }

    result = await mode_collection.insert_one(mode)
    mode["_id"] = str(result.inserted_id)

    return mode


async def get_mode(mode_id: str, user_id: str) -> Dict[str, Any]:
    mode = await _require_mode(mode_id, user_id)
    return _serialize(mode)


async def get_modes(user_id: str) -> List[Dict[str, Any]]:
    modes = (
        await mode_collection
        .find({"user_id": user_id})
        .sort("updated_at", -1)
        .to_list(length=None)
    )

    return [_serialize(mode) for mode in modes]


async def delete_mode(mode_id: str, user_id: str) -> Dict[str, Any]:
    await _require_mode(mode_id, user_id)

    await mode_collection.delete_one({"mode_id": mode_id, "user_id": user_id})

    await conversation_collection.update_many(
        {"mode_id": mode_id, "user_id": user_id},
        {
            "$set": {
                "mode_id": None,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    return {"message": "Mode deleted successfully"}