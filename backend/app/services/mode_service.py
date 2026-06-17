from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException

from app.database.mongodb import mode_collection
from app.schemas.mode_schema import ModeRequest


async def create_mode(data: ModeRequest):
    existing_mode = await mode_collection.find_one(
        {"title": data.title}
    )

    if existing_mode:
        raise HTTPException(
            status_code=400,
            detail="Mode title already exists"
        )

    mode = {
        "mode_id": str(uuid4()),
        "title": data.title,
        "description": data.description,
        "system_prompt": data.system_prompt,
        "updated_at": datetime.utcnow()
    }

    result = await mode_collection.insert_one(mode)

    mode["_id"] = str(result.inserted_id)

    return mode


async def get_modes():
    modes = []

    async for mode in mode_collection.find().sort(
        "updated_at",
        -1
    ):
        mode["_id"] = str(mode["_id"])
        modes.append(mode)

    return modes


async def get_mode(mode_id: str):
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


async def delete_mode(mode_id: str):
    result = await mode_collection.delete_one(
        {"mode_id": mode_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Mode not found"
        )

    return {
        "message": "Mode deleted successfully"
    }


async def edit_mode(
    mode_id: str,
    data: ModeRequest
):
    mode = await mode_collection.find_one(
        {"mode_id": mode_id}
    )

    if not mode:
        raise HTTPException(
            status_code=404,
            detail="Mode not found"
        )

    duplicate = await mode_collection.find_one(
        {
            "title": data.title,
            "mode_id": {"$ne": mode_id}
        }
    )

    if duplicate:
        raise HTTPException(
            status_code=400,
            detail="Mode title already exists"
        )

    await mode_collection.update_one(
        {"mode_id": mode_id},
        {
            "$set": {
                "title": data.title,
                "description": data.description,
                "system_prompt": data.system_prompt,
                "updated_at": datetime.utcnow()
            }
        }
    )

    updated_mode = await mode_collection.find_one(
        {"mode_id": mode_id}
    )

    updated_mode["_id"] = str(
        updated_mode["_id"]
    )

    return updated_mode