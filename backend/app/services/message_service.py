import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from app.database.mongodb import message_collection, mode_collection
from app.schemas.message_schema import MessageRequest
from app.services.conversation_service import _require_conversation
from app.services.langchain_provider import generate, generate_stream


async def get_context_messages(
    conversation_id: str,
    user_message: str,
    mode_id: Optional[str] = None,
) -> List[Dict[str, str]]:
    messages = (
        await message_collection
        .find({"conversation_id": conversation_id})
        .sort("sequence", -1)
        .limit(10)
        .to_list(length=10)
    )

    messages.reverse()

    context = [
        {"role": msg["role"], "content": msg["message"]}
        for msg in messages
    ]

    context.append({"role": "user", "content": user_message})

    if mode_id:
        mode = await mode_collection.find_one({"mode_id": mode_id})
        if mode and mode.get("system_prompt"):
            context.insert(0, {
                "role": "system",
                "content": mode["system_prompt"],
            })

    return context


async def generate_title(
    message: str,
    conversation_id: str,
    user_id: str,
    provider: str,
    model: str,
):
    title_prompt = f"""Generate a short conversation title in two to four words
based on the following user message.
User message: {message},
Only return the title.
Example: if the user message is "How do I reset my password?",
a good title would be "Password Reset Help". """

    try:
        generated_title = await generate(
            provider=provider,
            model=model,
            message=title_prompt,
        )

        generated_title = generated_title.strip().replace('"', "")

        if not generated_title:
            generated_title = "NEW CONVERSATION"

        await _update_conversation_title(
            conversation_id=conversation_id,
            user_id=user_id,
            title=generated_title,
        )

    except Exception:
        pass


async def _update_conversation_title(
    conversation_id: str,
    user_id: str,
    title: str,
) -> None:
    from app.database.mongodb import conversation_collection

    await conversation_collection.update_one(
        {"conversation_id": conversation_id, "user_id": user_id},
        {
            "$set": {
                "title": title,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def insert_message(
    conversation_id: str,
    role: str,
    message: str,
    sequence: int,
) -> None:
    document = {
        "conversation_id": conversation_id,
        "role": role,
        "message": message,
        "sequence": sequence,
        "timestamp": datetime.utcnow(),
    }

    await message_collection.insert_one(document)


async def send_message(data: MessageRequest, user_id: str) -> StreamingResponse:
    conversation = await _require_conversation(data.conversation_id, user_id)

    async def event_generator():
        provider = conversation["provider"]
        model = conversation["model"]
        mode_id = conversation.get("mode_id")

        context_messages = await get_context_messages(
            conversation_id=data.conversation_id,
            user_message=data.message,
            mode_id=mode_id,
        )

        start = time.time()
        full_response = ""
        first_chunk = True
        ttft_ms = 0.0
        llm_status = "success"
        error_message = None

        try:
            async for content in generate_stream(
                provider=provider,
                model=model,
                messages=context_messages
            ):
                if first_chunk:
                    ttft_ms = (time.time() - start) * 1000
                    first_chunk = False

                full_response += content
                yield f"data: {json.dumps({'content': content})}\n\n"

        except Exception as exc:
            llm_status = "error"
            error_message = str(exc)
            yield f"data: {json.dumps({'error': error_message})}\n\n"

        end = time.time()
        latency_ms = (end - start) * 1000

        sequence = await message_collection.count_documents(
            {"conversation_id": data.conversation_id}
        )

        await insert_message(
            conversation_id=data.conversation_id,
            role="user",
            message=data.message,
            sequence=sequence + 1,
        )

        if llm_status == "success" and full_response.strip():
            assistant_message = full_response
        else:
            assistant_message = f"Error generating response: {error_message}"

        await insert_message(
            conversation_id=data.conversation_id,
            role="assistant",
            message=assistant_message,
            sequence=sequence + 2,
        )

        await _update_conversation_title(
            conversation_id=data.conversation_id,
            user_id=user_id,
            title=conversation["title"],
        )

        if conversation.get("title") == "NEW CONVERSATION":
            await generate_title(
                message=data.message,
                conversation_id=data.conversation_id,
                user_id=user_id
            )

        yield (
            f"data: {json.dumps({'done': True, 'latency_ms': round(latency_ms, 2), 'ttft_ms': round(ttft_ms, 2)})}\n\n"
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


async def get_messages(
    conversation_id: str,
    user_id: str,
) -> List[Dict[str, Any]]:
    await _require_conversation(conversation_id, user_id)

    messages = (
        await message_collection
        .find({"conversation_id": conversation_id})
        .sort("sequence", 1)
        .to_list(length=None)
    )

    for msg in messages:
        msg["_id"] = str(msg["_id"])

    return messages