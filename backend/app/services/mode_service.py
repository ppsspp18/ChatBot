from datetime import datetime
from uuid import uuid4

from app.database.mongodb import modes_collection
from backend.app.schemas.mode_schema import ModeRequest


async def create_mode(data: ModeRequest):
    """
    Create a new mode
    """

    existing_mode = await modes_collection.find_one(
        {"title": data.title}
    )

    if existing_mode:
        return {
            "success": False,
            "message": "Mode title already exists"
        }

    mode = {
        "mode_id": str(uuid4()),
        "title": data.title,
        "description": data.description,
        "system_prompt": data.system_prompt,
        "created_at": datetime.utcnow()
    }

    await modes_collection.insert_one(mode)

    return {
        "success": True,
        "message": "Mode created successfully",
        "data": mode
    }


async def get_modes():
    """
    Get all modes
    """

    modes = await modes_collection.find(
        {},
        {"_id": 0}
    ).to_list(length=None)

    return {
        "success": True,
        "data": modes
    }


async def get_mode(mode_id: str):
    """
    Get single mode
    """

    mode = await modes_collection.find_one(
        {"mode_id": mode_id},
        {"_id": 0}
    )

    if not mode:
        return {
            "success": False,
            "message": "Mode not found"
        }

    return {
        "success": True,
        "data": mode
    }


async def delete_mode(mode_id: str):
    """
    Delete mode
    """

    result = await modes_collection.delete_one(
        {"mode_id": mode_id}
    )

    if result.deleted_count == 0:
        return {
            "success": False,
            "message": "Mode not found"
        }

    return {
        "success": True,
        "message": "Mode deleted successfully"
    }


async def edit_mode(mode_id: str, data: ModeRequest):
    """
    Edit existing mode
    """

    mode = await modes_collection.find_one(
        {"mode_id": mode_id}
    )

    if not mode:
        return {
            "success": False,
            "message": "Mode not found"
        }

    duplicate = await modes_collection.find_one({
        "title": data.title,
        "mode_id": {"$ne": mode_id}
    })

    if duplicate:
        return {
            "success": False,
            "message": "Mode title already exists"
        }

    await modes_collection.update_one(
        {"mode_id": mode_id},
        {
            "$set": {
                "title": data.title,
                "description": data.description,
                "system_prompt": data.system_prompt
            }
        }
    )

    updated_mode = await modes_collection.find_one(
        {"mode_id": mode_id},
        {"_id": 0}
    )

    return {
        "success": True,
        "message": "Mode updated successfully",
        "data": updated_mode
    }