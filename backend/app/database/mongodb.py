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
mode_collection = db["modes"]
quiz_collection = db["quizes"]
user_collection = db["users"]