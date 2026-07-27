from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ==========================
# Frontend Request
# ==========================
class QuizRequest(BaseModel):

    topic: str
    concept: str

    difficulty: Literal[
        "Easy",
        "Medium",
        "Hard"
    ]

    number_of_questions: int = Field(
        ...,
        ge=1,
        le=100
    )

    additional_description: Optional[str] = None


# ==========================
# LLM Response
# ==========================
class QuizQuestion(BaseModel):
    questionNo: int

    question: str

    options: List[str] = Field(
        ...,
        min_length=4,
        max_length=4
    )

    correctOption: int = Field(
        ...,
        ge=1,
        le=4,
        description="1-based index of the correct option"
    )


class QuizLLMResponse(BaseModel):
    title: str
    questions: List[QuizQuestion]


# ==========================
# Database Schema
# ==========================
class QuizSchema(BaseModel):
    session_id: str

    sequence: int

    topic: str
    concept: str
    difficulty: str

    title: str
    questions: List[QuizQuestion]

    inference_log_id: Optional[str] = None

    created_at: datetime