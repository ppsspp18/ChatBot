from datetime import datetime
from uuid import uuid4

from app.database.mongodb import mode_collection


# Validation
async def validate_mode(
    mode_id: str
):
    mode = await mode_collection.find_one(
        {"mode_id": mode_id}
    )

    if not mode:
        raise ValueError(
            "Mode not found"
        )

    return mode


async def validate_mode_title(
    title: str,
    exclude_mode_id: str = None
):
    query = {
        "title": title
    }

    if exclude_mode_id:
        query["mode_id"] = {
            "$ne": exclude_mode_id
        }

    mode = await mode_collection.find_one(
        query
    )

    if mode:
        raise ValueError(
            "Mode title already exists"
        )

    return True


# Create
async def create_mode_db(
    title: str,
    description: str,
    system_prompt: str
):
    mode = {
        "mode_id": str(uuid4()),
        "title": title,
        "description": description,
        "system_prompt": system_prompt,
        "updated_at": datetime.utcnow()
    }

    result = await mode_collection.insert_one(
        mode
    )

    mode["_id"] = str(
        result.inserted_id
    )

    return mode


# Read
async def get_mode_by_id(
    mode_id: str
):
    return await mode_collection.find_one(
        {"mode_id": mode_id}
    )


async def get_all_modes_db():
    modes = []

    async for mode in (
        mode_collection
        .find()
        .sort("updated_at", -1)
    ):
        mode["_id"] = str(
            mode["_id"]
        )

        modes.append(mode)

    return modes


# Update
async def update_mode(
    mode_id: str,
    title: str,
    description: str,
    system_prompt: str
):
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

    updated_mode["_id"] = str(
        updated_mode["_id"]
    )

    return updated_mode


# Delete
async def delete_mode_db(
    mode_id: str
):
    return await mode_collection.delete_one(
        {"mode_id": mode_id}
    )