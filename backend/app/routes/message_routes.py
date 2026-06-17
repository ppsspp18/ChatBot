from fastapi import APIRouter

from backend.app.schemas.message_schema import MessageRequest

from app.services.ollama_service import get_ollama_messages
from backend.app.services.message_service import send_message, get_messages

router = APIRouter(
    prefix="/messages",
    tags=["Messages"]
)

@router.post("/")
async def send_message_route(data: MessageRequest):
    return await send_message(data)

@router.post("/ollama")
async def get_ollama_messages_route(data: MessageRequest):
    return await get_ollama_messages(data)

@router.get("/")
async def get_messages_route(session_id: str):
    return await get_messages(session_id)
