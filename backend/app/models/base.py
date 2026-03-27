from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import timezone
from sqlalchemy import Column, DateTime, text


class TimestampMixin:
    """Mixin for timestamp fields."""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        nullable=False,
    )

class UserActionMixin:
    """Mixin for user action fields."""

    created_by: Optional[int] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)


class TenantMixin:
    """Mixin for tenant-related fields."""

    # tenant_id: str = Field(nullable=False)


class BaseModel(SQLModel, TenantMixin, TimestampMixin, UserActionMixin):
    """Base model with common fields."""

    pass
