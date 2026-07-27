from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import MONGO_URI, DATABASE_NAME

client = AsyncIOMotorClient(
    MONGO_URI,
    maxPoolSize=50,
    minPoolSize=10,
    serverSelectionTimeoutMS=5000
)

db = client[DATABASE_NAME]

conversation_collection = db["conversations"]
message_collection = db["messages"]
inference_log_collection = db["inference_logs"]
event_collection = db["events"]
mode_collection = db["modes"]
quiz_collection = db["quizes"]