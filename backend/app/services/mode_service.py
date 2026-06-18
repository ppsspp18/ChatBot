from fastapi import HTTPException

from app.crud.crud_mode import (
    validate_mode,
    validate_mode_title,
    create_mode_db,
    get_mode_by_id,
    get_all_modes_db,
    update_mode,
    delete_mode_db
)

from app.crud.crud_conversation import(
    remove_mode_from_conversations
)


async def create_mode(data):
    try:
        await validate_mode_title(
            data.title
        )

        return await create_mode_db(
            title=data.title,
            description=data.description,
            system_prompt=data.system_prompt
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


async def get_modes():
    return await get_all_modes_db()


async def get_mode(
    mode_id: str
):
    mode = await get_mode_by_id(
        mode_id
    )

    if not mode:
        raise HTTPException(
            status_code=404,
            detail="Mode not found"
        )

    mode["_id"] = str(
        mode["_id"]
    )

    return mode


async def edit_mode(
    mode_id: str,
    data
):
    try:
        await validate_mode(
            mode_id
        )

        await validate_mode_title(
            title=data.title,
            exclude_mode_id=mode_id
        )

        return await update_mode(
            mode_id=mode_id,
            title=data.title,
            description=data.description,
            system_prompt=data.system_prompt
        )

    except ValueError as e:
        if str(e) == "Mode not found":
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


async def delete_mode(
    mode_id: str
):
    try:
        await validate_mode(
            mode_id
        )

        await remove_mode_from_conversations(
            mode_id
        )

        result = await delete_mode_db(
            mode_id
        )

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Mode not found"
            )

        return {
            "message": "Mode deleted successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )