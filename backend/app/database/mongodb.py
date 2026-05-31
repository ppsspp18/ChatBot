from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import MONGO_URI, DATABASE_NAME

client = AsyncIOMotorClient(
    MONGO_URI,
    maxPoolSize=50,
    minPoolSize=10,
    serverSelectionTimeoutMS=5000
)

db = client[DATABASE_NAME]

conversations_collection = db["conversations"]
messages_collection = db["messages"]
inference_logs_collection = db["inference_logs"]
events_collection = db["events"]