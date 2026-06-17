from datetime import datetime
from uuid import uuid4

from app.database.mongodb import inference_log_collection


async def log_inference(
    session_id: str,
    provider: str,
    model: str,
    latency_ms: float,
    ttft_ms: float,
    prompt_tokens: int,
    completion_tokens: int,
    status: str,
    pii_detected: bool = False,
    entities: list[str] = [],
    input_preview: str = "",
    output_preview: str = ""
):

    log = {
        "log_id": str(uuid4()),

        "session_id": session_id,

        "provider": provider,
        "model": model,

        "latency_ms": latency_ms,
        "ttft_ms": ttft_ms,

        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,

        "status": status,

        "pii_detected": pii_detected,
        "entities": entities,

        "input_preview": input_preview[:200],
        "output_preview": output_preview[:200],

        "created_at": datetime.utcnow()
    }

    result = await inference_log_collection.insert_one(log)

    return {
        "inserted_id": str(result.inserted_id),
        "log_id": log["log_id"]
    }