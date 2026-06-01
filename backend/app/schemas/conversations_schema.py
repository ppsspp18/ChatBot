from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class CreateConversationRequest(BaseModel):
    title: str


class UpdateChatRequest(BaseModel):
    session_id: str
    title: str


class ConversationSchema(BaseModel):
    session_id: str
    title: str
    status: Literal["active", "cancelled", "done"]
    total_tokens: int
    created_at: datetime
    updated_at: datetime