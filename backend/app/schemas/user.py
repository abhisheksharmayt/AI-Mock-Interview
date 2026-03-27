from app.schemas.base import BaseCreate, BaseResponse
from datetime import datetime
from typing import Optional

class UserCreate(BaseCreate):
    """User create schema."""
    email: str
    password: str
    full_name: str


class UserResponse(BaseResponse):
    """User response schema."""
    email: str
    full_name: str
    is_active: bool
    last_login_at: Optional[datetime] = None
