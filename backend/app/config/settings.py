from dotenv import load_dotenv
import os

load_dotenv()

# App environment
APP_ENV = os.getenv("APP_ENV", "development").lower()

# API keys / providers
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Database
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# JWT Authentication
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)
)

# CORS
# Comma-separated list in env, e.g.
# CORS_ORIGINS=https://your-app.vercel.app,http://localhost:8501
raw_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000"
)

CORS_ORIGINS = [
    origin.strip()
    for origin in raw_cors_origins.split(",")
    if origin.strip()
]