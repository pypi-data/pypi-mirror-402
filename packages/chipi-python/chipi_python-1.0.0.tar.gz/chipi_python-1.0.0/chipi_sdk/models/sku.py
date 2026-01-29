"""SKU-related types and models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Sku(BaseModel):
    """SKU (Stock Keeping Unit) model."""
    
    id: str
    org_id: str
    name: str
    description: Optional[str] = None
    price: str
    currency: str
    metadata: Optional[dict] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GetSkuListQuery(BaseModel):
    """Query parameters for SKU list."""
    
    page: Optional[int] = Field(None, ge=1)
    limit: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None
