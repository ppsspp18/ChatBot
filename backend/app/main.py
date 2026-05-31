from fastapi import FastAPI
from app.routes.conversations_routes import router

app = FastAPI(
    title="AI Chat System"
)

app.include_router(router)

@app.get("/")
async def health():

    return {
        "status": "running"
    }