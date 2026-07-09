from fastapi import APIRouter

from app.schemas.mode_schema import ModeRequest

from app.crud.crud_mode import (
    create_mode,
    get_all_modes,
    get_mode,
    update_mode,
    delete_mode
)

router = APIRouter(
    prefix="/modes",
    tags=["Modes"]
)


@router.post("/")
async def create_mode_route(
    data: ModeRequest
):
    return await create_mode(
        title=data.title,
        description=data.description,
        system_prompt=data.system_prompt
    )


@router.get("/")
async def get_modes_route():
    return await get_all_modes()


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
    return await update_mode(
        mode_id=mode_id,
        title=data.title,
        description=data.description,
        system_prompt=data.system_prompt
    )


@router.delete("/{mode_id}")
async def delete_mode_route(
    mode_id: str
):
    return await delete_mode(mode_id)