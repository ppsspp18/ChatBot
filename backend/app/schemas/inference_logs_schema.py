from pydantic import BaseModel
from typing import Literal, List
from uuid import UUID


class InferenceLogSchema(BaseModel):
    session_id: str
    log_id: UUID

    provider: str
    model: str

    latency_ms: float
    ttft_ms: float

    prompt_tokens: int
    completion_tokens: int

    status: Literal["success", "error", "cancelled"]

    pii_detected: bool
    entities: List[str]

    input_preview: str
    output_preview: str