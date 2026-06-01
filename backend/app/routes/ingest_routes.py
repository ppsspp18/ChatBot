from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.ingestion.event_bus import event_bus
from app.ingestion.validator import IngestPayload

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("", status_code=202)
async def ingest_log(payload: dict):
    """
    Receive an inference log from the SDK or any external tool.
    Validates the payload, enqueues it onto the EventBus, and
    immediately returns 202 Accepted — the caller is never blocked
    by the DB write.

    The background worker (ingestion/worker.py) drains the queue and
    persists the log to MongoDB.
    """
    try:
        validated = IngestPayload(**payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    event = {
        "event_type": "inference_log",
        "session_id": validated.session_id,
        "data": validated.model_dump(),
    }

    await event_bus.put(event)

    return {
        "status": "accepted",
        "log_id": validated.log_id,
        "queue_size": event_bus.size,
    }


@router.get("/health", tags=["Ingestion"])
async def ingest_health():
    """Returns the current depth of the ingestion queue."""
    return {
        "status": "ok",
        "queue_size": event_bus.size,
    }
