import time, json
from uuid import uuid4, UUID
from datetime import datetime

from fastapi import HTTPException
from fastapi.responses import StreamingResponse


from app.database.mongodb import (
    conversations_collection,
    messages_collection
)

from app.services.llm_router import router
from app.services.inference_logger import log_inference


async def create_conversation(data):
    """
    data: CreateConversationRequest (has .title attribute)
    Bug fix: previous code called with a raw str from the route.
    """
    conversation = {
        "session_id": str(uuid4()),
        "title": data.title,
        "status": "active",
        "total_tokens": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    await conversations_collection.insert_one(conversation)

    conversation["_id"] = str(conversation["_id"])

    return conversation


async def edit_conversation(data):
    result = await conversations_collection.update_one(
        {"session_id": data.session_id},
        {
            "$set": {
                "title": data.title,
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "message": "Conversation updated successfully"
    }


async def get_all_conversations():
    conversations = []

    async for conversation in conversations_collection.find().sort("updated_at", -1):
        conversation["_id"] = str(conversation["_id"])
        conversations.append(conversation)

    return conversations


async def get_conversation(session_id: str):
    conversation = await conversations_collection.find_one(
        {"session_id": session_id}
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    conversation["_id"] = str(conversation["_id"])

    return conversation


async def cancel_conversation(session_id: str):
    """
    Soft-cancel: sets status to 'cancelled', keeps all messages intact.
    The frontend can still resume the conversation (history preserved).
    """
    result = await conversations_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": "cancelled",
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "message": "Conversation cancelled successfully",
        "session_id": str(session_id)
    }


async def delete_conversation(session_id: str):
    result = await conversations_collection.delete_one(
        {"session_id": session_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    await messages_collection.delete_many(
        {"session_id": str(session_id)}
    )

    return {
        "message": "Conversation deleted successfully"
    }


async def send_message(data):
    conversation = await conversations_collection.find_one(
        {"session_id": data.session_id}
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    if conversation.get("status") == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cannot send messages to a cancelled conversation. Resume it first."
        )

    recent_messages = (
        await messages_collection
        .find({"session_id": data.session_id})
        .sort("sequence", -1)
        .limit(10)
        .to_list(length=10)
    )

    recent_messages.reverse()

    # Bug fix: stored field is "message", not "content"
    context_messages = []
    for msg in recent_messages:
        context_messages.append({
            "role": msg["role"],
            "content": msg["message"]
        })

    context_messages.append({
        "role": "user",
        "content": data.message
    })

    start = time.time()

    try:
        response = await router.generate(
            provider=data.provider,
            model=data.model,
            messages=context_messages
        )
        llm_status = "success"
        error_message = None
    except Exception as exc:
        llm_status = "error"
        error_message = str(exc)
        raise HTTPException(status_code=502, detail=f"LLM provider error: {exc}")
    finally:
        end = time.time()

    end = time.time()
    latency_ms = (end - start) * 1000
    ttft_ms = latency_ms

    # Token estimation (char-based, as per the deepseek formula already in place)
    prompt_tokens = int(len(data.message) * 0.3)
    completion_tokens = int(len(response) * 0.3)
    total_tokens = prompt_tokens + completion_tokens

    sequence = await messages_collection.count_documents(
        {"session_id": data.session_id}
    )

    # Save user message
    user_message = {
        "session_id": data.session_id,
        "role": "user",
        "message": data.message,
        "provider": data.provider,
        "model": data.model,
        "sequence": sequence + 1,
        "timestamp": datetime.utcnow(),
        "inference_log_id": None
    }

    await messages_collection.insert_one(user_message)

    # Save inference log
    inference_result = await log_inference(
        session_id=data.session_id,
        provider=data.provider,
        model=data.model,
        latency_ms=latency_ms,
        ttft_ms=ttft_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        status=llm_status,
        pii_detected=False,
        entities=[],
        input_preview=data.message,
        output_preview=response
    )

    # Save assistant message
    assistant_message = {
        "session_id": data.session_id,
        "role": "assistant",
        "message": response,
        "provider": data.provider,
        "model": data.model,
        "sequence": sequence + 2,
        "timestamp": datetime.utcnow(),
        "inference_log_id": inference_result["log_id"]
    }

    await messages_collection.insert_one(assistant_message)

    # Update conversation token count
    await conversations_collection.update_one(
        {"session_id": data.session_id},
        {
            "$set": {
                "updated_at": datetime.utcnow()
            },
            "$inc": {
                "total_tokens": total_tokens
            }
        }
    )

    return {
        "response": response,
        "latency_ms": round(latency_ms, 2)
    }


async def send_message_stream(data):

    async def event_generator():

        conversation = await conversations_collection.find_one(
            {"session_id": data.session_id}
        )

        if not conversation:
            yield f"data: {json.dumps({'error': 'Conversation not found'})}\n\n"
            return

        if conversation.get("status") == "cancelled":
            yield f"data: {json.dumps({'error': 'Conversation is cancelled'})}\n\n"
            return

        recent_messages = (
            await messages_collection
            .find({"session_id": data.session_id})
            .sort("sequence", -1)
            .limit(10)
            .to_list(length=10)
        )

        recent_messages.reverse()

        # Bug fix: stored field is "message", not "content"
        context_messages = []
        for msg in recent_messages:
            context_messages.append({
                "role": msg["role"],
                "content": msg["message"]
            })

        context_messages.append({
            "role": "user",
            "content": data.message
        })

        start = time.time()
        full_response = ""
        first_chunk = True
        ttft_ms = 0.0
        llm_status = "success"
        error_message = None

        try:
            async for chunk in router.generate_stream(
                provider=data.provider,
                model=data.model,
                messages=context_messages
            ):
                if first_chunk:
                    ttft_ms = (time.time() - start) * 1000
                    first_chunk = False

                full_response += chunk
                yield f"data: {json.dumps({'token': chunk})}\n\n"

        except Exception as exc:
            llm_status = "error"
            error_message = str(exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

        end = time.time()
        latency_ms = (end - start) * 1000

        prompt_tokens = int(len(data.message) * 0.3)
        completion_tokens = int(len(full_response) * 0.3)
        total_tokens = prompt_tokens + completion_tokens

        sequence = await messages_collection.count_documents(
            {"session_id": data.session_id}
        )

        user_message = {
            "session_id": data.session_id,
            "role": "user",
            "message": data.message,
            "provider": data.provider,
            "model": data.model,
            "sequence": sequence + 1,
            "timestamp": datetime.utcnow(),
            "inference_log_id": None
        }

        await messages_collection.insert_one(user_message)

        inference_result = await log_inference(
            session_id=data.session_id,
            provider=data.provider,
            model=data.model,
            latency_ms=latency_ms,
            ttft_ms=ttft_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            status=llm_status,
            pii_detected=False,
            entities=[],
            input_preview=data.message,
            output_preview=full_response
        )

        if full_response:
            assistant_message = {
                "session_id": data.session_id,
                "role": "assistant",
                "message": full_response,
                "provider": data.provider,
                "model": data.model,
                "sequence": sequence + 2,
                "timestamp": datetime.utcnow(),
                "inference_log_id": inference_result["log_id"]
            }
            await messages_collection.insert_one(assistant_message)

        await conversations_collection.update_one(
            {"session_id": data.session_id},
            {
                "$set": {"updated_at": datetime.utcnow()},
                "$inc": {"total_tokens": total_tokens}
            }
        )

        yield f"data: {json.dumps({'done': True, 'latency_ms': round(latency_ms, 2), 'ttft_ms': round(ttft_ms, 2)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


async def get_messages(session_id: str):
    messages = []

    async for message in messages_collection.find(
        {"session_id": session_id}
    ).sort("sequence", 1):

        message["_id"] = str(message["_id"])
        if message.get("inference_log_id"):
            message["inference_log_id"] = str(message["inference_log_id"])
        messages.append(message)

    return messages
