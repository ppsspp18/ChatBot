from fastapi import APIRouter

from app.schemas.mode_schema import ModeRequest

from app.services.mode_service import (
    create_mode,
    get_modes,
    get_mode,
    delete_mode,
    edit_mode
)

router = APIRouter(
    prefix="/modes",
    tags=["Modes"]
)


@router.post("/")
async def create_mode_route(
    data: ModeRequest
):
    return await create_mode(data)


@router.get("/")
async def get_modes_route():
    return await get_modes()


@router.get("/{mode_id}")
async def get_mode_route(
    mode_id: str
):
    return await get_mode(mode_id)


@router.patch("/{mode_id}")
async def edit_mode_route(
    mode_id: str,
    data: ModeRequest
):
    return await edit_mode(
        mode_id,
        data
    )


@router.delete("/{mode_id}")
async def delete_mode_route(
    mode_id: str
):
    return await delete_mode(
        mode_id
    )