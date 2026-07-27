# routes/quiz_route.py
from typing import List, Any

from fastapi import APIRouter

from app.schemas.quiz_schema import QuizRequest
from app.services.quiz_service import create_quiz, get_all_quizzes

router = APIRouter(
    prefix="/quiz",
    tags=["Quiz"]
)


@router.post("/")
async def create_quiz_route(data: QuizRequest) -> Any:
    return await create_quiz(data)


@router.get("/")
async def get_all_quizzes_route() -> List[Any]:
    return await get_all_quizzes()