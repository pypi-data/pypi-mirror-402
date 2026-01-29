"""User-related types and models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateUserParams(BaseModel):
    """Parameters for creating a user."""
    
    external_user_id: str = Field(..., description="External user identifier")
    email: Optional[str] = Field(None, description="User email")
    metadata: Optional[dict] = Field(None, description="Additional user metadata")


class GetUserParams(BaseModel):
    """Parameters for retrieving a user."""
    
    external_user_id: str = Field(..., description="External user identifier")


class User(BaseModel):
    """User model."""
    
    id: str
    org_id: str
    external_user_id: str
    email: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
