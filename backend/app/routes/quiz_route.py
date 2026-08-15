from typing import Any, List

from fastapi import APIRouter, Depends, Request

from app.core.security import get_current_user
from app.schemas.quiz_schema import QuizRequest
from app.services.quiz_service import create_quiz, delete_quiz, get_all_quizzes
from app.core.limiter import limiter

router = APIRouter(
    prefix="/quiz",
    tags=["Quiz"],
)


@router.post("/")
@limiter.limit("2/minute")
async def create_quiz_route(
    request: Request,
    data: QuizRequest,
    current_user: Any = Depends(get_current_user),
) -> Any:
    return await create_quiz(data, current_user["user_id"])


@router.get("/")
async def get_all_quizzes_route(
    current_user: Any = Depends(get_current_user),
) -> List[Any]:
    return await get_all_quizzes(current_user["user_id"])

@router.delete("/{quiz_id}")
async def delete_quiz_route(
    quiz_id: str,
    current_user: Any = Depends(get_current_user),
) -> Any:
    return await delete_quiz(quiz_id, current_user["user_id"])