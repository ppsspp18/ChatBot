from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional
from datetime import datetime
from bson import ObjectId


class MessageRequest(BaseModel):
    session_id: str
    message: str

class MessageSchema(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    session_id: str
    role: Literal[
        "user",
        "assistant",
        "system"
    ]
    message: str
    sequence: int
    timestamp: datetime
    inference_log_id: Optional[ObjectId] = None