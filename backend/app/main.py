import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import CORS_ORIGINS
from app.database.indexes import create_indexes

from app.routes.auth_routes import router as auth_router
from app.routes.conversation_routes import router as conversations_router
from app.routes.message_routes import router as messages_router
from app.routes.mode_routes import router as modes_router
from app.routes.quiz_route import router as quiz_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    try:
        await create_indexes()
    except Exception as exc:
        logger.warning("Index creation failed (non-fatal): %s", exc)


    yield

    logger.info("Shutting down...")


app = FastAPI(
    title="LLM ChatBot API",
    description=(
        "Chatbot backend with multi-provider LLM support (Groq + Google AI Studio), "
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

app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(messages_router)
app.include_router(modes_router)
app.include_router(quiz_router)


@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "running",
        "service": "AI ChatBot",
    }