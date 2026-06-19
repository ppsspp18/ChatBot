import time, json
from uuid import uuid4
from datetime import datetime
from typing import Optional

from fastapi.responses import StreamingResponse


from app.database.mongodb import (
    message_collection,
) 

#changes : validate mode before adding in conversation

from app.services.langchain_provider import generate_stream, generate
from app.services.inference_logger import log_inference

from app.crud.crud_conversation import(
    validate_conversation,
    update_conversation,
)

from app.crud.crud_mode import(
    validate_mode,
)

async def get_context_messages(
    session_id: str,
    user_message: str,
    mode_id: Optional[str] = None,
):
    
    messages = (
        await message_collection
        .find({"session_id": session_id})
        .sort("sequence", -1)
        .limit(10)
        .to_list(length=10)
    )

    messages.reverse()

    context = [
        {
            "role": msg["role"],
            "content": msg["message"]
        }
        for msg in messages
    ]

    context.append({
        "role": "user",
        "content": user_message
    })

    if mode_id: 
        mode = await validate_mode(mode_id)
        system_prompt = mode["system_prompt"]
        context.insert(0,{
            "role" : "system",
            "content" : system_prompt
        })

    return context


async def generate_title(data):
            title_prompt = f"""Generate a short conversation title in two to four words 
based on the following user message. 
User message: {data.message}, 
Only return the title.
Example: if the user message is "How do I reset my password?", 
a good title would be "Password Reset Help". """

            title_start = time.time()

            try:

                generated_title = await generate(
                    provider="groq",
                    model="openai/gpt-oss-20b",
                    message=title_prompt
                )
                
                title_end = time.time()

                title_latency_ms = (title_end - title_start) * 1000
                title_ttft_ms = title_latency_ms

                generated_title = generated_title.strip().replace('"', '')
                if not generated_title:
                    generated_title = "NEW CONVERSATION"

                title_prompt_tokens = int(len(title_prompt) * 0.3)
                title_completion_tokens = int(len(generated_title) * 0.3)
                title_total_tokens = (
                    title_prompt_tokens +
                    title_completion_tokens
                )

                await log_inference(
                    session_id=data.session_id,
                    provider="groq",
                    model="openai/gpt-oss-20b",
                    latency_ms=title_latency_ms,
                    ttft_ms=title_ttft_ms,
                    prompt_tokens=title_prompt_tokens,
                    completion_tokens=title_completion_tokens,
                    status="success",
                    pii_detected=False,
                    entities=[],
                    input_preview=title_prompt,
                    output_preview=generated_title
                )

                await update_conversation(
                    session_id=data.session_id, 
                    title=generated_title,
                    total_tokens=title_total_tokens
                    )

            except Exception as exc:

                title_end = time.time()

                title_latency_ms = (
                    title_end - title_start
                ) * 1000

                await log_inference(
                    session_id=data.session_id,
                    provider="groq",
                    model="openai/gpt-oss-20b",
                    latency_ms=title_latency_ms,
                    ttft_ms=title_latency_ms,
                    prompt_tokens=int(len(title_prompt) * 0.3),
                    completion_tokens=0,
                    status="error",
                    pii_detected=False,
                    entities=[],
                    input_preview=title_prompt,
                    output_preview=str(exc)
                )



async def send_message(data):

    async def event_generator():

        conversation = await validate_conversation(
             session_id=data.session_id
            )

        title = conversation["title"]
        provider = conversation["provider"]
        model = conversation["model"]
        mode_id = conversation["mode_id"]


        context_messages = await get_context_messages(
            session_id=data.session_id,
            user_message=data.message,
            mode_id=mode_id
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
        prompt_text = json.dumps(context_messages) 
        prompt_tokens = int(len(prompt_text) * 0.3)
        completion_tokens = int(len(full_response) * 0.3)
        total_tokens = prompt_tokens + completion_tokens

        sequence = await message_collection.count_documents(
            {"session_id": data.session_id}
        )

        user_message = {
            "session_id": data.session_id,
            "role": "user",
            "message": data.message,
            "provider": provider,
            "model": model,
            "sequence": sequence + 1,
            "timestamp": datetime.utcnow(),
            "inference_log_id": None
        }

        await message_collection.insert_one(user_message)

        inference_result = await log_inference(
            session_id=data.session_id,
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            ttft_ms=ttft_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            status=llm_status,
            pii_detected=False,
            entities=[],
            input_preview=data.message,
            output_preview=full_response
        )

        assistant_message = {
                "session_id": data.session_id,
                "role": "assistant",
                "message": full_response,
                "provider": provider,
                "model": model,
                "sequence": sequence + 2,
                "timestamp": datetime.utcnow(),
                "inference_log_id": inference_result["log_id"]
            }
        if(llm_status == "success" and full_response.strip()):
            await message_collection.insert_one(assistant_message)
        else:
            assistant_message["message"] = f"Error generating response: {error_message}" 
            await message_collection.insert_one(assistant_message)

        await update_conversation(
            session_id=data.session_id,
            title=title,
            total_tokens=total_tokens
            )

        if conversation.get("title") == "NEW CONVERSATION":
            await generate_title(data)


        yield f"data: {json.dumps({'done': True, 'latency_ms': round(latency_ms, 2), 'ttft_ms': round(ttft_ms, 2)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


async def get_messages(session_id: str):
    messages = []

    async for message in message_collection.find(
        {"session_id": session_id}
    ).sort("sequence", 1):

        message["_id"] = str(message["_id"])
        if message.get("inference_log_id"):
            message["inference_log_id"] = str(message["inference_log_id"])
        messages.append(message)

    return messages

async def get_message_simple(message : str):
    content = await generate(
                    provider="ollama",
                    model="gemma3:1b",
                    message=message
                )
    return  content

async def get_stream_simple(message : str):
    async def event_generator():
        full_response = ""
        async for content in generate_stream(
            provider="ollama",
            model="qwen3:0.6b",
            messages=[ {
                     "role":"user",
                     "content":message
            }
            ] 
            ):  
                full_response += content
                yield f"data: {json.dumps({'content': content})}\n\n"
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )        