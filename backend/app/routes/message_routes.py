from fastapi import APIRouter

from app.schemas.message_schema import MessageRequest
from app.services.message_service import( 
    send_message, 
    get_messages, 
    get_message_simple,
    get_stream_simple
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

@router.get("/ollama/{message}")
async def get_response_routes(message :str):
    return await get_message_simple(message)

@router.get("/ollama/stream/{message}")
async def get_response_routes_stream(message:str):
    return await get_stream_simple(message)