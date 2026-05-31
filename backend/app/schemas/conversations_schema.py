from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Literal


class CreateChatRequest(BaseModel):
    title: str
    provider: str
    model: str

class UpdateChatRequest(BaseModel):
    session_id: str
    title: str


class ConversationSchema(BaseModel):
    session_id: str
    title: str
    status: Literal["active", "cancelled", "done"]
    provider: str
    model: str
    total_tokens: int
    created_at: datetime
    updated_at: datetime