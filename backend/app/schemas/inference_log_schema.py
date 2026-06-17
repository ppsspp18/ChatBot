from pydantic import BaseModel
from typing import Literal, List


class InferenceLogSchema(BaseModel):
    session_id: str
    log_id: str

    provider: str
    model: str

    latency_ms: float
    ttft_ms: float

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    status: Literal["success", "error", "cancelled"]

    pii_detected: bool
    entities: List[str]

    input_preview: str
    output_preview: str