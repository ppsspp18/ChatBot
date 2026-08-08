from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ModeRequest(BaseModel):
    title: str
    description: str
    system_prompt: str


class ModeSchema(BaseModel):
    user_id: str
    mode_id: str
    title: str
    description: str
    system_prompt: str
    updated_at: datetime
