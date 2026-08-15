from typing import Any

from fastapi import APIRouter, Depends, Request

from app.core.security import get_current_user
from app.schemas.message_schema import MessageRequest
from app.services.message_service import get_messages, send_message
from app.core.limiter import limiter

router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
)


@router.post("/")
@limiter.limit("5/minute")
async def send_message_route(
    request: Request,
    data: MessageRequest,
    current_user: Any = Depends(get_current_user),
):
    return await send_message(data, current_user["user_id"])


@router.get("/{conversation_id}")
async def get_messages_route(
    conversation_id: str,
    current_user: Any = Depends(get_current_user),
):
    return await get_messages(conversation_id, current_user["user_id"])