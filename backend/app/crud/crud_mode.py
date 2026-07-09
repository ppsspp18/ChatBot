from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any

from fastapi import HTTPException

from app.database.mongodb import mode_collection


# Validation
async def validate_mode(
    mode_id: str
) -> Dict[str, Any]:
    mode = await mode_collection.find_one(
        {"mode_id": mode_id}
    )

    if not mode:
        raise HTTPException(
            status_code=404,
            detail="Mode not found"
        )

    mode["_id"] = str(mode["_id"])
    return mode


async def validate_mode_title(
    title: str,
    exclude_mode_id: str = None
) -> bool:
    query = {"title": title}

    if exclude_mode_id:
        query["mode_id"] = {"$ne": exclude_mode_id}

    mode = await mode_collection.find_one(query)

    if mode:
        raise HTTPException(
            status_code=400,
            detail="Mode title already exists"
        )

    return True


# Create
async def create_mode(
    title: str,
    description: str,
    system_prompt: str
) -> Dict[str, Any]:
    await validate_mode_title(title)

    mode = {
        "mode_id": str(uuid4()),
        "title": title,
        "description": description,
        "system_prompt": system_prompt,
        "updated_at": datetime.utcnow()
    }

    result = await mode_collection.insert_one(mode)
    mode["_id"] = str(result.inserted_id)

    return mode


# Read
async def get_mode(
    mode_id: str
) -> Dict[str, Any]:
    return await validate_mode(mode_id)


async def get_all_modes() -> List[Dict[str, Any]]:
    modes = []

    async for mode in (
        mode_collection
        .find()
        .sort("updated_at", -1)
    ):
        mode["_id"] = str(mode["_id"])
        modes.append(mode)

    return modes


# Update
async def update_mode(
    mode_id: str,
    title: str,
    description: str,
    system_prompt: str
) -> Dict[str, Any]:
    await validate_mode(mode_id)
    await validate_mode_title(title, exclude_mode_id=mode_id)

    await mode_collection.update_one(
        {"mode_id": mode_id},
        {
            "$set": {
                "title": title,
                "description": description,
                "system_prompt": system_prompt,
                "updated_at": datetime.utcnow()
            }
        }
    )

    updated_mode = await mode_collection.find_one(
        {"mode_id": mode_id}
    )
    updated_mode["_id"] = str(updated_mode["_id"])

    return updated_mode


# Delete
async def delete_mode(
    mode_id: str
) -> Dict[str, str]:
    await validate_mode(mode_id)

    await mode_collection.delete_one(
        {"mode_id": mode_id}
    )

    return {"message": "Mode deleted successfully"}