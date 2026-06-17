import logging
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.database.mongodb import (
    conversation_collection,
    message_collection,
    inference_log_collection,
    event_collection,
)

logger = logging.getLogger(__name__)


async def create_indexes() -> None:
    """
    Create MongoDB indexes.
    Safe to call on every application startup.
    """

    # ── conversations ──────────────────────────────────────────────
    await conversation_collection.create_indexes([
        IndexModel(
            [("session_id", ASCENDING)],
            unique=True,
            name="session_id_unique"
        ),
        IndexModel(
            [("status", ASCENDING)],
            name="status"
        ),
        IndexModel(
            [("provider", ASCENDING)],
            name="provider"
        ),
        IndexModel(
            [("model", ASCENDING)],
            name="model"
        ),
        IndexModel(
            [("mode_id", ASCENDING)],
            name="mode_id"
        ),
        IndexModel(
            [("created_at", DESCENDING)],
            name="created_at_desc"
        ),
        IndexModel(
            [("updated_at", DESCENDING)],
            name="updated_at_desc"
        ),

        # Common dashboard query:
        # active conversations for a provider
        IndexModel(
            [("provider", ASCENDING), ("status", ASCENDING)],
            name="provider_status"
        ),
    ])

    # ── messages ──────────────────────────────────────────────────
    await message_collection.create_indexes([
        IndexModel(
            [("session_id", ASCENDING)],
            name="session_id"
        ),

        # Retrieve conversation history in order
        IndexModel(
            [("session_id", ASCENDING), ("sequence", ASCENDING)],
            unique=True,
            name="session_sequence_unique"
        ),

        IndexModel(
            [("role", ASCENDING)],
            name="role"
        ),

        IndexModel(
            [("timestamp", DESCENDING)],
            name="timestamp_desc"
        ),

        IndexModel(
            [("inference_log_id", ASCENDING)],
            name="inference_log_id"
        ),
    ])

    # ── inference_logs ────────────────────────────────────────────
    await inference_log_collection.create_indexes([
        IndexModel(
            [("log_id", ASCENDING)],
            unique=True,
            name="log_id_unique"
        ),
        IndexModel(
            [("session_id", ASCENDING)],
            name="session_id"
        ),
        IndexModel(
            [("provider", ASCENDING)],
            name="provider"
        ),
        IndexModel(
            [("status", ASCENDING)],
            name="status"
        ),
        IndexModel(
            [("provider", ASCENDING), ("created_at", DESCENDING)],
            name="provider_created_at"
        ),
        IndexModel(
            [("created_at", DESCENDING)],
            name="created_at_desc"
        ),
    ])

    # ── events ────────────────────────────────────────────────────
    await event_collection.create_indexes([
        IndexModel(
            [("event_id", ASCENDING)],
            unique=True,
            name="event_id_unique"
        ),
        IndexModel(
            [("event_type", ASCENDING)],
            name="event_type"
        ),
        IndexModel(
            [("processed", ASCENDING)],
            name="processed"
        ),
        IndexModel(
            [("session_id", ASCENDING)],
            name="session_id"
        ),
        IndexModel(
            [("created_at", DESCENDING)],
            name="created_at_desc"
        ),
    ])

    logger.info("MongoDB indexes created / verified")