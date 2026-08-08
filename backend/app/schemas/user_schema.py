from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserSchema(BaseModel):
    user_id: str
    username: str
    hashed_password: str
    created_at: datetime


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: str
    username: str
    created_at: Optional[datetime] = None