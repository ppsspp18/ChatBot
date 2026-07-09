import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import CORS_ORIGINS
from app.ingestion.event_bus import event_bus
from app.ingestion.worker import worker_loop
from app.database.indexes import create_indexes

from app.routes.conversation_routes import router as conversations_router
from app.routes.message_routes import router as messages_router
from app.routes.mode_routes import router as modes_router
from app.routes.ingest_routes import router as ingest_router
from app.routes.metric_routes import router as metrics_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    event_bus.init()

    try:
        await create_indexes()
    except Exception as exc:
        logger.warning("Index creation failed (non-fatal): %s", exc)

    worker_task = asyncio.create_task(worker_loop(), name="ingestion-worker")
    logger.info("Ingestion worker started")

    yield

    logger.info("Shutting down...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    logger.info("Ingestion worker stopped")


app = FastAPI(
    title="LLM Inference Logger API",
    description=(
        "Chatbot backend with multi-provider LLM support (Groq + Google AI Studio), "
        "inference logging, ingestion pipeline, and metrics aggregation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversations_router)
app.include_router(messages_router)
app.include_router(modes_router)
app.include_router(ingest_router)
app.include_router(metrics_router)


@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "running",
        "service": "llm-inference-logger",
        "ingestion_queue_size": event_bus.size,
    }