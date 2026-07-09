from fastapi import APIRouter

from app.schemas.conversation_schema import (
    CreateConversationRequest,
    UpdateConversationRequest
)

from app.crud.crud_conversation import (
    create_conversation,
    update_conversation,
    get_all_conversations,
    get_conversation,
    update_conversation_status,
    delete_conversation
)

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)


@router.post("/")
async def create_conversation_route(
    data: CreateConversationRequest
):
    return await create_conversation(
        title=data.title,
        provider=data.provider,
        model=data.model,
        mode_id=data.mode_id
    )


@router.patch("/")
async def edit_conversation_route(
    data: UpdateConversationRequest
):
    await update_conversation(
        session_id=data.session_id,
        title=data.title,
        provider=data.provider,
        model=data.model,
        mode_id=data.mode_id
    )
    return {"message": "Conversation updated successfully"}


@router.get("/")
async def get_conversations_route():
    return await get_all_conversations()


@router.get("/{session_id}")
async def get_conversation_route(
    session_id: str
):
    return await get_conversation(session_id)


@router.patch("/cancel/{session_id}")
async def cancel_conversation_route(
    session_id: str
):
    return await update_conversation_status(
        session_id,
        "cancelled"
    )


@router.patch("/activate/{session_id}")
async def activate_conversation_route(
    session_id: str
):
    return await update_conversation_status(
        session_id,
        "active"
    )


@router.delete("/{session_id}")
async def delete_conversation_route(
    session_id: str
):
    return await delete_conversation(session_id)