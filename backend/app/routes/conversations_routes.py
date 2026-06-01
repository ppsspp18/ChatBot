from fastapi import APIRouter
from uuid import UUID

from app.schemas.conversations_schema import CreateConversationRequest, UpdateChatRequest
from app.schemas.messages_schema import MessageRequest

from app.services.conversations_service import (
    create_conversation,
    edit_conversation,
    get_all_conversations,
    get_conversation,
    cancel_conversation,
    delete_conversation,
    send_message,
    send_message_stream,
    get_messages
)

router = APIRouter(tags=["Conversations"])


# ── Conversations ─────────────────────────────────────────────────────────────

@router.post("/conversations/add")
async def create_chat_route(data: CreateConversationRequest):
    """Create a new conversation session."""
    return await create_conversation(data)


@router.post("/conversations/edit")
async def edit_chat_route(data: UpdateChatRequest):
    """Rename a conversation."""
    return await edit_conversation(data)


@router.get("/conversations/all")
async def get_chats_route():
    """List all conversations, most recently updated first."""
    return await get_all_conversations()


@router.get("/conversations/get")
async def get_conversation_route(session_id: UUID):
    """Get a single conversation by session_id."""
    return await get_conversation(session_id)


@router.patch("/conversations/cancel")
async def cancel_conversation_route(session_id: UUID):
    """
    Soft-cancel a conversation (sets status=cancelled).
    Messages are preserved so the conversation can be resumed.
    """
    return await cancel_conversation(session_id)


@router.delete("/conversations/delete")
async def delete_conversation_route(session_id: UUID):
    """Hard-delete a conversation and all its messages."""
    return await delete_conversation(session_id)


# ── Messages ──────────────────────────────────────────────────────────────────

@router.post("/messages/send")
async def send_message_route(data: MessageRequest):
    """Send a message and get a synchronous (non-streaming) response."""
    return await send_message(data)


@router.post("/messages/send/stream")
async def send_message_stream_route(data: MessageRequest):
    """Send a message and receive a streaming SSE response."""
    return await send_message_stream(data)


@router.get("/messages/all")
async def get_messages_route(session_id: UUID):
    """Fetch all messages in a conversation ordered by sequence."""
    return await get_messages(session_id)
