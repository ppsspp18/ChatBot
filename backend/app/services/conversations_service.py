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
    conversation = {
        "session_id": str(uuid4()),
        "title": data.title,
        "provider": data.provider,
        "model": data.model,
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

    async for conversation in conversations_collection.find():
        conversation["_id"] = str(conversation["_id"])
        conversations.append(conversation)

    return conversations


async def get_conversation(session_id: UUID):
    conversation = await conversations_collection.find_one(
        {"session_id": str(session_id)}
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    conversation["_id"] = str(conversation["_id"])

    return conversation


async def delete_conversation(session_id: UUID):
    result = await conversations_collection.delete_one(
        {"session_id": str(session_id)}
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
    
    recent_messages = (
        await messages_collection
        .find({"session_id": data.session_id})
        .sort("sequence", -1)
        .limit(4)
        .to_list(length=4)
    )

    recent_messages.reverse()

    context_messages = []

    for msg in recent_messages:
        context_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    context_messages.append({
        "role": "user",
        "content": data.message
    })


    start = time.time()

    # Generate AI response
    response = await router.generate(
        provider=data.provider,
        model=data.model,
        messages=context_messages
    )

    end = time.time()

    latency_ms = (end - start) * 1000
    ttft_ms = latency_ms

    prompt_tokens = len(data.message.split())
    completion_tokens = len(response.split())

    sequence = await messages_collection.count_documents(
        {"session_id": data.session_id}
    )

    # Save user message
    user_message = {
        "session_id": data.session_id,
        "role": "user",
        "content": data.message,
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
        status="success",
        pii_detected=False,
        entities=[],
        input_preview=data.message,
        output_preview=response
    )

    # Save assistant message
    assistant_message = {
        "session_id": data.session_id,
        "role": "assistant",
        "content": response,
        "sequence": sequence + 2,
        "timestamp": datetime.utcnow(),
        "inference_log_id": inference_result["log_id"]
    }

    await messages_collection.insert_one(assistant_message)

    # Update conversation
    await conversations_collection.update_one(
        {"session_id": data.session_id},
        {
            "$set": {
                "updated_at": datetime.utcnow()
            },
            "$inc": {
                "total_tokens": prompt_tokens + completion_tokens
            }
        }
    )

    return {
        "response": response,
        "latency_ms": latency_ms
    }

async def send_message_stream(data):

    async def event_generator():

        conversation = await conversations_collection.find_one(
            {"session_id": data.session_id}
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        recent_messages = (
            await messages_collection
            .find({"session_id": data.session_id})
            .sort("sequence", -1)
            .limit(4)
            .to_list(length=4)
        )

        recent_messages.reverse()

        context_messages = []

        for msg in recent_messages:
            context_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        context_messages.append({
            "role": "user",
            "content": data.message
        })

        start = time.time()

        full_response = ""

        async for chunk in router.generate_stream(
            provider=data.provider,
            model=data.model,
            messages=context_messages
        ):

            full_response += chunk

            yield f"data: {json.dumps({'token': chunk})}\n\n"

        end = time.time()

        latency_ms = (end - start) * 1000
        ttft_ms = latency_ms

        prompt_tokens = len(data.message.split())
        completion_tokens = len(full_response.split())

        sequence = await messages_collection.count_documents(
            {"session_id": data.session_id}
        )


        user_message = {
            "session_id": data.session_id,
            "role": "user",
            "content": data.message,
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
            status="success",
            pii_detected=False,
            entities=[],
            input_preview=data.message,
            output_preview=full_response
        )

        assistant_message = {
            "session_id": data.session_id,
            "role": "assistant",
            "content": full_response,
            "sequence": sequence + 2,
            "timestamp": datetime.utcnow(),
            "inference_log_id": inference_result["log_id"]
        }

        await messages_collection.insert_one(assistant_message)

        await conversations_collection.update_one(
            {"session_id": data.session_id},
            {
                "$set": {
                    "updated_at": datetime.utcnow()
                },
                "$inc": {
                    "total_tokens": prompt_tokens + completion_tokens
                }
            }
        )

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


async def get_messages(session_id: UUID):
    messages = []

    async for message in messages_collection.find(
        {"session_id": str(session_id)}
    ).sort("sequence", 1):

        message["_id"] = str(message["_id"])
        messages.append(message)

    return messages