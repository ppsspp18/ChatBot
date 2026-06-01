from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any


class EventSchema(BaseModel):
    event_id: str
    event_type: str
    session_id: str
    payload: Dict[str, Any]
    processed: bool
    created_at: datetime