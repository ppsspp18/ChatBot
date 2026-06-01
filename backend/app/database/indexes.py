import logging
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.database.mongodb import (
    conversations_collection,
    messages_collection,
    inference_logs_collection,
    events_collection,
)

logger = logging.getLogger(__name__)


async def create_indexes() -> None:
    """
    Idempotent index creation — safe to call every startup.
    Motor / MongoDB silently skips indexes that already exist
    with the same options.
    """

    # ── conversations ────────────────────────────────────────────────────────
    await conversations_collection.create_indexes([
        IndexModel([("session_id", ASCENDING)], unique=True, name="session_id_unique"),
        IndexModel([("status",     ASCENDING)], name="status"),
        IndexModel([("created_at", DESCENDING)], name="created_at_desc"),
        IndexModel([("updated_at", DESCENDING)], name="updated_at_desc"),
    ])

    # ── messages ─────────────────────────────────────────────────────────────
    await messages_collection.create_indexes([
        IndexModel([("session_id", ASCENDING)],  name="session_id"),
        # Compound index for ordered retrieval per conversation
        IndexModel(
            [("session_id", ASCENDING), ("sequence", ASCENDING)],
            name="session_sequence",
        ),
        IndexModel([("timestamp", DESCENDING)], name="timestamp_desc"),
    ])

    # ── inference_logs ───────────────────────────────────────────────────────
    await inference_logs_collection.create_indexes([
        IndexModel([("log_id",     ASCENDING)], unique=True, name="log_id_unique"),
        IndexModel([("session_id", ASCENDING)], name="session_id"),
        IndexModel([("provider",   ASCENDING)], name="provider"),
        IndexModel([("status",     ASCENDING)], name="status"),
        # Compound index for dashboard time-range queries per provider
        IndexModel(
            [("provider", ASCENDING), ("created_at", DESCENDING)],
            name="provider_created_at",
        ),
        IndexModel([("created_at", DESCENDING)], name="created_at_desc"),
    ])

    # ── events ───────────────────────────────────────────────────────────────
    await events_collection.create_indexes([
        IndexModel([("event_id",   ASCENDING)], unique=True, name="event_id_unique"),
        IndexModel([("event_type", ASCENDING)], name="event_type"),
        IndexModel([("processed",  ASCENDING)], name="processed"),
        IndexModel([("session_id", ASCENDING)], name="session_id"),
        IndexModel([("created_at", DESCENDING)], name="created_at_desc"),
    ])

    logger.info("MongoDB indexes created / verified")
