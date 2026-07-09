from fastapi import APIRouter

from app.schemas.message_schema import MessageRequest
from app.services.message_service import( 
    send_message, 
    get_messages, 
)

router = APIRouter(
    prefix="/messages",
    tags=["Messages"]
)

@router.post("/")
async def send_message_route(data: MessageRequest):
    return await send_message(data)

@router.get("/{session_id}")
async def get_messages_route(session_id: str):
    return await get_messages(session_id)