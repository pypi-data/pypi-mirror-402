"""SKU transaction types and models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateSkuTransactionParams(BaseModel):
    """Parameters for creating a SKU transaction."""
    
    sku_id: str = Field(..., description="SKU identifier")
    wallet_address: str = Field(..., description="Buyer wallet address")
    quantity: int = Field(1, ge=1, description="Quantity to purchase")
    metadata: Optional[dict] = Field(None, description="Additional transaction metadata")


class SkuTransaction(BaseModel):
    """SKU transaction record."""
    
    id: str
    sku_id: str
    wallet_address: str
    transaction_hash: Optional[str] = None
    quantity: int
    total_price: str
    currency: str
    status: str
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
