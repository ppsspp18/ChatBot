from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional
from datetime import datetime
from bson import ObjectId

class MessageRequest(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    session_id: str
    message: str
    provider: str
    model: str

class MessageSchema(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    session_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    sequence: int
    timestamp: datetime
    inference_log_id: Optional[ObjectId] = None
