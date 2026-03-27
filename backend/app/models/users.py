from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Numeric, String, text
from sqlmodel import Field, SQLModel

from app.models.base import BaseModel


class User(BaseModel, table=True):
    __tablename__ = "user"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(nullable=False, unique=True)
    password_hash: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    last_login_at: Optional[datetime] = Field(default=None)


class UserProfile(BaseModel, table=True):
    """extension for user-facing profile fields (keeps `users` small)."""

    __tablename__ = "user_profile"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False, unique=True)
    headline: Optional[str] = Field(default=None, sa_column=Column(String(512), nullable=True))
    target_role: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    years_of_experience: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(4, 1), nullable=True),
    )
    current_company: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
