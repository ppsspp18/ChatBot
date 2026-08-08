from datetime import datetime
from typing import Literal, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict


class MessageRequest(BaseModel):
    conversation_id: str
    message: str


class MessageSchema(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    conversation_id: str
    role: Literal[
        "user",
        "assistant",
        "system"
    ]
    message: str
    sequence: int
    timestamp: datetime
