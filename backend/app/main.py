import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ingestion.event_bus import event_bus
from app.ingestion.worker import worker_loop
from app.database.indexes import create_indexes

from backend.app.routes.conversation_routes import router as conversations_router
from app.routes.messages_routes import router as messages_router
from app.routes.modes_routes import router as modes_router
from app.routes.ingest_routes import router as ingest_router
from backend.app.routes.metric_routes import router as metrics_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("Starting up...")

    # 1. Initialise the event bus queue (must happen inside the running loop)
    event_bus.init()

    # 2. Create MongoDB indexes (idempotent — safe to run on every restart)
    try:
        await create_indexes()
    except Exception as exc:
        logger.warning("Index creation failed (non-fatal): %s", exc)

    # 3. Start the background ingestion worker
    worker_task = asyncio.create_task(worker_loop(), name="ingestion-worker")
    logger.info("Ingestion worker started")

    yield

    # Shutdown 
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

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten to your Render/Vercel URLs in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(conversations_router)
app.include_router(messages_router)
app.include_router(modes_router)
app.include_router(ingest_router)
app.include_router(metrics_router)

# Health 
@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "running",
        "service": "llm-inference-logger",
        "ingestion_queue_size": event_bus.size,
    }
