import json
import time
import uuid
from datetime import datetime
from typing import Any, List

from fastapi import HTTPException

from app.database.mongodb import quiz_collection
from app.schemas.quiz_schema import QuizLLMResponse, QuizRequest
from app.services.langchain_provider_quiz import generate_quiz


def build_quiz_prompt(data: QuizRequest) -> str:
    prompt = f"""
Generate a multiple-choice quiz.

Topic: {data.topic}
Concept: {data.concept}
Difficulty: {data.difficulty}
Number of Questions: {data.number_of_questions}
"""

    if data.additional_description:
        prompt += (
            f"\nAdditional Instructions: "
            f"{data.additional_description}\n"
        )

    prompt += """

Return ONLY valid JSON in the following format:

{
  "title": "Quiz Title",
  "questions": [
    {
      "questionNo": 1,
      "question": "Question",
      "options": ["A","B","C","D"],
      "correctOption": 2
    }
  ]
}

Rules:
- Exactly the requested number of questions.
- Exactly 4 options.
- correctOption must be between 1 and 4.
- Return only valid JSON.
"""

    return prompt.strip()


async def create_quiz(data: QuizRequest, user_id: str) -> Any:
    prompt = build_quiz_prompt(data)
    start = time.time()

    try:
        response = await generate_quiz(prompt)

        if isinstance(response, str):
            response = json.loads(response)

        try:
            validated_response = QuizLLMResponse(**response)
        except Exception as validation_error:
            raise ValueError(
                f"LLM response failed Pydantic validation: {validation_error}"
            )

        quiz_document = {
            "quiz_id": str(uuid.uuid4()),
            "user_id": user_id,
            "topic": data.topic,
            "concept": data.concept,
            "difficulty": data.difficulty,
            "questions": [
                q.model_dump() for q in validated_response.questions
            ],
            "created_at": datetime.utcnow(),
            "latency_ms": round((time.time() - start) * 1000, 2),
        }

        result = await quiz_collection.insert_one(quiz_document)
        quiz_document["_id"] = str(result.inserted_id)

        return quiz_document

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


async def get_all_quizzes(user_id: str) -> List[Any]:
    quizzes = (
        await quiz_collection
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .to_list(length=None)
    )

    for quiz in quizzes:
        quiz["_id"] = str(quiz["_id"])

    return quizzes