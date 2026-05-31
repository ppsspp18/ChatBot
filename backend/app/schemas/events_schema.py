from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Dict, Any


class EventSchema(BaseModel):
    event_id: UUID
    event_type: str
    session_id: str
    payload: Dict[str, Any]
    processed: bool
    created_at: datetime