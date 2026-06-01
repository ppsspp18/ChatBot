from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, Optional
from datetime import datetime


class IngestPayload(BaseModel):
    """
    Strict schema for payloads hitting POST /ingest.
    Extra fields are forbidden so malformed SDK versions fail fast.
    """

    model_config = {"extra": "forbid"}

    session_id: str = Field(..., min_length=1, max_length=128)
    log_id: str = Field(..., min_length=1)

    provider: Literal["groq", "google"]
    model: str = Field(..., min_length=1, max_length=128)

    latency_ms: float = Field(..., ge=0)
    ttft_ms: float = Field(..., ge=0)

    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)

    status: Literal["success", "error", "cancelled"]
    error_message: Optional[str] = Field(default=None, max_length=1000)

    pii_detected: bool = False
    entities: List[str] = []

    input_preview: str = Field(default="", max_length=200)
    output_preview: str = Field(default="", max_length=200)

    created_at: Optional[datetime] = None

    @field_validator("total_tokens")
    @classmethod
    def total_must_match(cls, v, info):
        data = info.data
        prompt = data.get("prompt_tokens", 0)
        completion = data.get("completion_tokens", 0)
        # Allow slight mismatch (some providers round differently)
        if abs(v - (prompt + completion)) > 5:
            raise ValueError(
                f"total_tokens ({v}) does not match "
                f"prompt_tokens + completion_tokens ({prompt + completion})"
            )
        return v

    @field_validator("input_preview", "output_preview")
    @classmethod
    def truncate_previews(cls, v):
        return v[:200] if v else ""


class EventPayload(BaseModel):
    """Internal event structure put onto the EventBus."""

    event_type: Literal[
        "inference_log",
        "inference_error",
        "conversation_cancelled",
    ]
    session_id: str
    data: dict
