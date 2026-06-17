from pydantic import BaseModel
from datetime import datetime

class ModeRequest(BaseModel):
    title: str
    description: str
    system_prompt: str

class ModeSchema(BaseModel):
    mode_id: str
    title: str
    description: str
    system_prompt: str
    updated_at: datetime