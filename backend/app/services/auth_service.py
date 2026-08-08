import uuid
from datetime import datetime

from fastapi import HTTPException, status

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.database.mongodb import user_collection
from app.schemas.user_schema import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)


async def register(data: RegisterRequest) -> UserResponse:
    existing = await user_collection.find_one({"username": data.username})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    user_id = str(uuid.uuid4())

    user_document = {
        "user_id": user_id,
        "username": data.username,
        "hashed_password": hash_password(data.password),
        "created_at": datetime.utcnow(),
    }

    await user_collection.insert_one(user_document)

    return UserResponse(
        user_id=user_id,
        username=data.username,
        created_at=user_document["created_at"],
    )


async def authenticate(data: LoginRequest) -> TokenResponse:
    user = await user_collection.find_one({"username": data.username})

    if user is None or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        user_id=user["user_id"],
        username=user["username"],
    )

    return TokenResponse(access_token=token)


async def get_user_by_id(user_id: str) -> UserResponse:
    user = await user_collection.find_one({"user_id": user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        user_id=user["user_id"],
        username=user["username"],
        created_at=user.get("created_at"),
    )