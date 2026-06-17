from fastapi import APIRouter

from backend.app.schemas.conversation_schema import CreateConversationRequest, UpdateChatRequest

from backend.app.services.conversation_service import (
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
async def create_chat_route(data: CreateConversationRequest):
    return await create_conversation(data)


@router.patch("/")
async def edit_chat_route(data: UpdateChatRequest):
    return await edit_conversation(data)


@router.get("/")
async def get_chats_route():
    return await get_all_conversations()


@router.get("/{session_id}")
async def get_conversation_route(session_id: str):
    return await get_conversation(session_id)


@router.patch("/cancel/{session_id}")
async def cancel_conversation_route(session_id: str):
    return await cancel_conversation(session_id)

@router.patch("/activate/{session_id}")
async def activate_conversation_route(session_id: str):
    return await activate_conversation(session_id)


@router.delete("/{session_id}")
async def delete_conversation_route(session_id: str):
    return await delete_conversation(session_id)
