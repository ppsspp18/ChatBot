from typing import Any

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.schemas.conversation_schema import (
    CreateConversationRequest,
    UpdateConversationRequest,
)
from app.services import conversation_service

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post("/")
async def create_conversation_route(
    data: CreateConversationRequest,
    current_user: Any = Depends(get_current_user),
):
    return await conversation_service.create_conversation(
        data, current_user["user_id"]
    )


@router.patch("/")
async def edit_conversation_route(
    data: UpdateConversationRequest,
    current_user: Any = Depends(get_current_user),
):
    return await conversation_service.update_conversation(
        data, current_user["user_id"]
    )


@router.get("/")
async def get_conversations_route(
    current_user: Any = Depends(get_current_user),
):
    return await conversation_service.get_conversations(current_user["user_id"])


@router.get("/{conversation_id}")
async def get_conversation_route(
    conversation_id: str,
    current_user: Any = Depends(get_current_user),
):
    return await conversation_service.get_conversation(
        conversation_id, current_user["user_id"]
    )

@router.delete("/{conversation_id}")
async def delete_conversation_route(
    conversation_id: str,
    current_user: Any = Depends(get_current_user),
):
    return await conversation_service.delete_conversation(
        conversation_id, current_user["user_id"]
    )
