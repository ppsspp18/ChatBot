import asyncio
import logging
from datetime import datetime
from uuid import uuid4

from app.ingestion.event_bus import event_bus
from app.database.mongodb import inference_logs_collection, events_collection

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


async def _persist_inference_log(data: dict) -> None:
    """Write a validated inference log into MongoDB."""
    log = {
        "log_id":            data.get("log_id", str(uuid4())),
        "session_id":        data["session_id"],
        "provider":          data["provider"],
        "model":             data["model"],
        "latency_ms":        data["latency_ms"],
        "ttft_ms":           data["ttft_ms"],
        "prompt_tokens":     data["prompt_tokens"],
        "completion_tokens": data["completion_tokens"],
        "total_tokens":      data["total_tokens"],
        "status":            data["status"],
        "error_message":     data.get("error_message"),
        "pii_detected":      data.get("pii_detected", False),
        "entities":          data.get("entities", []),
        "input_preview":     data.get("input_preview", "")[:200],
        "output_preview":    data.get("output_preview", "")[:200],
        "created_at":        data.get("created_at") or datetime.utcnow(),
        "source":            "ingest_api",          # marks external ingestion
    }
    await inference_logs_collection.insert_one(log)
    logger.debug("Persisted inference log %s", log["log_id"])


async def _record_event(event_type: str, session_id: str, payload: dict,
                        status: str = "processed") -> None:
    """Write a lifecycle event to the events collection."""
    await events_collection.insert_one({
        "event_id":   str(uuid4()),
        "event_type": event_type,
        "session_id": session_id,
        "payload":    payload,
        "processed":  status == "processed",
        "status":     status,
        "retries":    payload.get("_retries", 0),
        "created_at": datetime.utcnow(),
    })


async def _process_event(event: dict) -> None:
    """Dispatch a single event to the appropriate handler."""
    event_type = event.get("event_type")
    session_id = event.get("session_id", "unknown")
    data = event.get("data", {})

    if event_type == "inference_log":
        await _persist_inference_log(data)
        await _record_event(event_type, session_id, data, status="processed")

    elif event_type == "inference_error":
        # Still persist so errors show up in dashboards
        data["status"] = "error"
        await _persist_inference_log(data)
        await _record_event(event_type, session_id, data, status="processed")

    elif event_type == "conversation_cancelled":
        await _record_event(event_type, session_id, data, status="processed")

    else:
        logger.warning("Unknown event_type: %s — skipping", event_type)


async def worker_loop() -> None:
    """
    Infinite loop that drains the event bus queue.
    Started as an asyncio.Task inside the FastAPI lifespan.
    Failed events are retried up to MAX_RETRIES times,
    then written to the events collection with status='failed'.
    """
    logger.info("Ingestion worker started")

    while True:
        event = await event_bus.get()
        retries = event.get("_retries", 0)

        try:
            await _process_event(event)
        except Exception as exc:
            logger.error(
                "Worker failed to process event (attempt %d/%d): %s",
                retries + 1, MAX_RETRIES, exc,
                exc_info=True,
            )
            if retries < MAX_RETRIES - 1:
                # Re-queue with incremented retry counter
                event["_retries"] = retries + 1
                await event_bus.put(event)
            else:
                # Dead-letter: persist as failed for manual inspection
                try:
                    await _record_event(
                        event_type=event.get("event_type", "unknown"),
                        session_id=event.get("session_id", "unknown"),
                        payload={**event.get("data", {}), "error": str(exc)},
                        status="failed",
                    )
                except Exception as inner:
                    logger.critical("Dead-letter write also failed: %s", inner)
        finally:
            event_bus.task_done()
