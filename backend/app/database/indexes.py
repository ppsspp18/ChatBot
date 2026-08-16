import logging
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.database.mongodb import (
    conversation_collection,
    message_collection,
    mode_collection,
    quiz_collection,
    user_collection,
)

logger = logging.getLogger(__name__)


async def create_indexes() -> None:
    """
    Create MongoDB indexes.
    Safe to call on every application startup.
    """

    # ── users ─────────────────────────────────────────────────────
    await user_collection.create_indexes([
        IndexModel(
            [("user_id", ASCENDING)],
            unique=True,
            name="user_id_unique"
        ),
        IndexModel(
            [("username", ASCENDING)],
            unique=True,
            name="username_unique"
        ),
    ])

    # ── conversations ──────────────────────────────────────────────
    await conversation_collection.create_indexes([
        IndexModel(
            [("conversation_id", ASCENDING)],
            unique=True,
            name="conversation_id_unique"
        ),
        IndexModel(
            [("user_id", ASCENDING), ("updated_at", DESCENDING)],
            name="user_id_updated_at"
        ),
    ])

    # ── messages ──────────────────────────────────────────────────
    await message_collection.create_indexes([
        IndexModel(
            [("conversation_id", ASCENDING), ("sequence", ASCENDING)],
            unique=True,
            name="conversation_sequence_unique"
        ),
    ])

    # ── modes ─────────────────────────────────────────────────────
    await mode_collection.create_indexes([
        IndexModel(
            [("mode_id", ASCENDING)],
            unique=True,
            name="mode_id_unique"
        ),
    

        IndexModel(
            [("user_id", ASCENDING), ("mode_id", ASCENDING)],
            unique=True,
            name="user_mode_unique"
        ),
    ])

    # ── quizzes ───────────────────────────────────────────────────
    await quiz_collection.create_indexes([
        IndexModel(
            [("quiz_id", ASCENDING)],
            unique=True,
            name="quiz_id_unique"
        ),

        IndexModel(
            [("user_id", ASCENDING), ("created_at", DESCENDING)],
            name="user_created_at"
        ),
    ])

    logger.info("MongoDB indexes created / verified")