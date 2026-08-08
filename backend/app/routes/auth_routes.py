from typing import Any

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.schemas.user_schema import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import register, authenticate, get_user_by_id

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/register", response_model=UserResponse)
async def register_route(data: RegisterRequest) -> UserResponse:
    return await register(data)


@router.post("/login", response_model=TokenResponse)
async def login_route(data: LoginRequest) -> TokenResponse:
    return await authenticate(data)


@router.get("/me", response_model=UserResponse)
async def me_route(current_user: Any = Depends(get_current_user)) -> UserResponse:
    return await get_user_by_id(current_user["user_id"])