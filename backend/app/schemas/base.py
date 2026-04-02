from datetime import datetime
from typing import Optional, Union
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """Base response schema with common fields."""

    model_config = ConfigDict(from_attributes=True)

    id: Union[UUID, int]  # Support both UUID and integer IDs
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

class BaseCreate(BaseModel):
    """Base create schema with common fields."""
    
    pass

class BaseUpdate(BaseModel):
    """Base update schema with common fields."""
    
    pass