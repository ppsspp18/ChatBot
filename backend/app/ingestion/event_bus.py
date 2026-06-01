import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class EventBus:
    """
    In-process async event bus backed by asyncio.Queue.
    Must be initialized inside the FastAPI lifespan (after the event loop starts).
    Swap put/get for Redis Streams in production for durability.
    """

    def __init__(self):
        self._queue: asyncio.Queue = None

    def init(self, maxsize: int = 0):
        """Call once inside the FastAPI lifespan startup block."""
        self._queue = asyncio.Queue(maxsize=maxsize)
        logger.info("EventBus initialized")

    async def put(self, event: Dict[str, Any]) -> None:
        if self._queue is None:
            raise RuntimeError("EventBus not initialized. Call init() first.")
        await self._queue.put(event)

    async def get(self) -> Dict[str, Any]:
        if self._queue is None:
            raise RuntimeError("EventBus not initialized. Call init() first.")
        return await self._queue.get()

    def task_done(self) -> None:
        if self._queue is not None:
            self._queue.task_done()

    @property
    def size(self) -> int:
        return self._queue.qsize() if self._queue else 0


# Module-level singleton — import this everywhere
event_bus = EventBus()
