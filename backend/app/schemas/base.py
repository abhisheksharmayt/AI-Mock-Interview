from datetime import datetime
from typing import Optional, Union
from uuid import UUID
from pydantic import BaseModel

class BaseResponse(BaseModel):
    """Base response schema with common fields."""

    id: Union[UUID, int]  # Support both UUID and integer IDs
    created_at: datetime
    updated_at: datetime
    created_by: int

class BaseCreate(BaseModel):
    """Base create schema with common fields."""
    
    pass

class BaseUpdate(BaseModel):
    """Base update schema with common fields."""
    
    pass