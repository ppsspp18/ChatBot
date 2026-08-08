from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


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
    questions: List[QuizQuestion]


class QuizSchema(BaseModel):
    quiz_id: str
    user_id: str
    topic: str
    concept: str
    difficulty: str
    questions: List[QuizQuestion]
    created_at: datetime
