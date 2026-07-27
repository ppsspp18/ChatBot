import json
import time
import uuid
from datetime import datetime
from typing import Any, List, Optional

from fastapi import HTTPException

from app.database.mongodb import quiz_collection
from app.services.langchain_provider_quiz import generate_quiz
from app.services.inference_logger import log_inference
from app.schemas.quiz_schema import QuizRequest, QuizLLMResponse


QUIZ_PROVIDER = "groq"  
QUIZ_MODEL = "llama-3.3-70b-versatile"  


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


def generate_session_id() -> str:
    """Generate a unique session ID using UUID4 with timestamp prefix."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4().hex[:12])
    return f"quiz_{timestamp}_{unique_id}"


async def create_quiz(data: QuizRequest) -> Any:
    # Generate session ID if not provided
    session_id = generate_session_id()
    
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

        latency_ms = (time.time() - start) * 1000

        # Better token estimation using response length
        response_json = validated_response.model_dump_json()
        prompt_tokens = len(prompt.split())  # Rough estimation
        completion_tokens = len(response_json.split())

        inference = await log_inference(
            session_id=session_id,
            provider=QUIZ_PROVIDER,
            model=QUIZ_MODEL,
            latency_ms=latency_ms,
            ttft_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            status="success",
            pii_detected=False,
            entities=[],
            input_preview=prompt,
            output_preview=response_json
        )

        sequence = (
            await quiz_collection.count_documents(
                {"session_id": session_id}
            )
        ) + 1

        quiz_document = {
            "session_id": session_id,
            "sequence": sequence,
            "topic": data.topic,
            "concept": data.concept,
            "difficulty": data.difficulty,
            "title": validated_response.title,
            "questions": [q.model_dump() for q in validated_response.questions],
            "created_at": datetime.utcnow(),
            "inference_log_id": inference["log_id"],
        }

        result = await quiz_collection.insert_one(quiz_document)

        quiz_document["_id"] = str(result.inserted_id)
        quiz_document["inference_log_id"] = str(
            quiz_document["inference_log_id"]
        )

        return quiz_document

    except Exception as exc:

        latency_ms = (time.time() - start) * 1000

        await log_inference(
            session_id=session_id,
            provider=QUIZ_PROVIDER,
            model=QUIZ_MODEL,
            latency_ms=latency_ms,
            ttft_ms=latency_ms,
            prompt_tokens=len(prompt.split()),
            completion_tokens=0,
            status="error",
            pii_detected=False,
            entities=[],
            input_preview=prompt,
            output_preview=str(exc)
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


async def get_all_quizzes() -> List[Any]:
    quizzes = (
        await quiz_collection.find()
        .sort("created_at", -1)
        .to_list(length=None)
    )

    for quiz in quizzes:
        quiz["_id"] = str(quiz["_id"])

        if quiz.get("inference_log_id"):
            quiz["inference_log_id"] = str(
                quiz["inference_log_id"]
            )

    return quizzes