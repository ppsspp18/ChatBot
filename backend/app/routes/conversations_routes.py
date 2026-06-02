from fastapi import APIRouter

from app.schemas.conversations_schema import CreateConversationRequest, UpdateChatRequest
from app.schemas.messages_schema import MessageRequest

from app.services.conversations_service import (
    create_conversation,
    edit_conversation,
    get_all_conversations,
    get_conversation,
    cancel_conversation,
    activate_conversation,
    delete_conversation,
    send_message,
    send_message_stream,
    get_messages
)

router = APIRouter(tags=["Conversations"])


# ── Conversations ─────────────────────────────────────────────────────────────

@router.post("/conversations/add")
async def create_chat_route(data: CreateConversationRequest):
    return await create_conversation(data)


@router.post("/conversations/edit")
async def edit_chat_route(data: UpdateChatRequest):
    return await edit_conversation(data)


@router.get("/conversations/all")
async def get_chats_route():
    return await get_all_conversations()


@router.get("/conversations/get")
async def get_conversation_route(session_id: str):
    return await get_conversation(session_id)


@router.patch("/conversations/cancel")
async def cancel_conversation_route(session_id: str):
    return await cancel_conversation(session_id)

@router.patch("/conversations/activate")
async def activate_conversation_route(session_id: str):
    return await activate_conversation(session_id)


@router.delete("/conversations/delete")
async def delete_conversation_route(session_id: str):
    return await delete_conversation(session_id)

@router.post("/messages/send")
async def send_message_route(data: MessageRequest):
    return await send_message(data)


@router.post("/messages/send/stream")
async def send_message_stream_route(data: MessageRequest):
    return await send_message_stream(data)


@router.get("/messages/all")
async def get_messages_route(session_id: str):
    return await get_messages(session_id)
