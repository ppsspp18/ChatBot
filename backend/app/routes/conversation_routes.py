from fastapi import APIRouter

from app.schemas.conversation_schema import (
    CreateConversationRequest,
    UpdateConversationRequest
)

from app.services.conversation_service import (
    create_conversation,
    edit_conversation,
    get_all_conversations,
    get_conversation,
    cancel_conversation,
    activate_conversation,
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
    return await create_conversation(data)


@router.patch("/")
async def edit_conversation_route(
    data: UpdateConversationRequest
):
    return await edit_conversation(data)


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
    return await cancel_conversation(session_id)


@router.patch("/activate/{session_id}")
async def activate_conversation_route(
    session_id: str
):
    return await activate_conversation(session_id)


@router.delete("/{session_id}")
async def delete_conversation_route(
    session_id: str
):
    return await delete_conversation(session_id)