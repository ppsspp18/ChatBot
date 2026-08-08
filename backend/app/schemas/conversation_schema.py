from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreateConversationRequest(BaseModel):
    title: str
    provider: str
    model: str
    mode_id: Optional[str] = None


class UpdateConversationRequest(BaseModel):
    conversation_id: str
    title: str


class ConversationSchema(BaseModel):
    conversation_id: str
    user_id: str
    title: str
    provider: str
    model: str
    mode_id: Optional[str] = None
    total_tokens: int
    created_at: datetime
    updated_at: datetime
