from fastapi import APIRouter
from uuid import UUID

from app.schemas.conversations_schema import CreateChatRequest
from app.schemas.messages_schema import MessageRequest

from app.services.conversations_service import (
    create_conversation,
    get_all_conversations,
    get_conversation,
    delete_conversation,
    send_message,
    get_messages
)

router = APIRouter()


@router.post("/conversations/add")
async def create_chat_route(data: CreateChatRequest):
    return await create_conversation(data)


@router.get("/conversations/all")
async def get_chats_route():
    return await get_all_conversations()


@router.get("/conversations/get")
async def get_conversation_route(session_id: UUID):
    return await get_conversation(session_id)


@router.delete("/conversations/delete")
async def delete_conversation_route(session_id: UUID):
    return await delete_conversation(session_id)


@router.post("/messages/send")
async def send_message_route(
    data: MessageRequest
):
    return await send_message(data)


@router.get("/messages/all")
async def get_messages_route(session_id: UUID):
    return await get_messages(session_id)