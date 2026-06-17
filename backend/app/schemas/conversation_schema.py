from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional


class CreateConversationRequest(BaseModel):
    title: str
    provider: str
    model: str
    mode_id: Optional[str] = None


class UpdateConversationRequest(BaseModel):
    session_id: str
    title: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    mode_id: Optional[str] = None


class ConversationSchema(BaseModel):
    session_id: str
    title: str
    provider: str
    model: str
    mode_id: Optional[str] = None
    status: Literal["active", "cancelled", "done"]
    total_tokens: int
    created_at: datetime
    updated_at: datetime