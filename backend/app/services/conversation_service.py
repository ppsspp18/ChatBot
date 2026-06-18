from fastapi import HTTPException

from app.crud.crud_conversation import (
    validate_conversation,
    create_conversation_db,
    get_conversation_by_session_id,
    get_all_conversations_db,
    update_conversation,
    update_conversation_status,
    delete_conversation_db
)

from app.database.mongodb import (
    message_collection
)


async def create_conversation(data):
    return await create_conversation_db(
        title=data.title,
        provider=data.provider,
        model=data.model,
        mode_id=data.mode_id
    )


async def edit_conversation(data):
    try:
        await validate_conversation(
            data.session_id,
            allow_cancelled=True
        )

        await update_conversation(
            session_id=data.session_id,
            title=data.title,
            provider=data.provider,
            model=data.model,
            mode_id=data.mode_id
        )

        return {
            "message": "Conversation updated successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


async def get_all_conversations():
    return await get_all_conversations_db()


async def get_conversation(
    session_id: str
):
    conversation = await get_conversation_by_session_id(
        session_id
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
    try:
        await validate_conversation(
            session_id,
            allow_cancelled=True
        )

        await update_conversation_status(
            session_id,
            "cancelled"
        )

        return {
            "message": "Conversation cancelled successfully",
            "session_id": session_id
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


async def activate_conversation(
    session_id: str
):
    try:
        await validate_conversation(
            session_id,
            allow_cancelled=True
        )

        await update_conversation_status(
            session_id,
            "active"
        )

        return {
            "message": "Conversation activated successfully",
            "session_id": session_id
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


async def delete_conversation(
    session_id: str
):
    try:
        await validate_conversation(
            session_id,
            allow_cancelled=True
        )

        result = await delete_conversation_db(
            session_id
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

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )