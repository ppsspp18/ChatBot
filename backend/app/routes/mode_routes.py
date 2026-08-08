from typing import Any

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.schemas.mode_schema import ModeRequest
from app.services import mode_service

router = APIRouter(
    prefix="/modes",
    tags=["Modes"],
)


@router.post("/")
async def create_mode_route(
    data: ModeRequest,
    current_user: Any = Depends(get_current_user),
):
    return await mode_service.create_mode(data, current_user["user_id"])


@router.get("/")
async def get_modes_route(
    current_user: Any = Depends(get_current_user),
):
    return await mode_service.get_modes(current_user["user_id"])


@router.get("/{mode_id}")
async def get_mode_route(
    mode_id: str,
    current_user: Any = Depends(get_current_user),
):
    return await mode_service.get_mode(mode_id, current_user["user_id"])


@router.delete("/{mode_id}")
async def delete_mode_route(
    mode_id: str,
    current_user: Any = Depends(get_current_user),
):
    return await mode_service.delete_mode(mode_id, current_user["user_id"])