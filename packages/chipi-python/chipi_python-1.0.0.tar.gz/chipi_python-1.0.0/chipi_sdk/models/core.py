"""Core configuration and base types for Chipi SDK."""

from enum import Enum
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field


class Chain(str, Enum):
    """Supported blockchain networks."""
    STARKNET = "STARKNET"


class ChainToken(str, Enum):
    """Supported token types."""
    USDC_E = "USDC_E"
    USDC = "USDC"
    USDT = "USDT"
    ETH = "ETH"
    STRK = "STRK"
    DAI = "DAI"
    WBTC = "WBTC"
    OTHER = "OTHER"


class ChipiSDKConfig(BaseModel):
    """Configuration for initializing the Chipi SDK."""
    
    api_public_key: str = Field(..., description="Public API key for authentication")
    alpha_url: Optional[str] = Field(None, description="Optional custom API URL")
    node_url: Optional[str] = Field(None, description="Optional custom Starknet node URL")
    api_secret_key: Optional[str] = Field(None, description="Optional API secret key for server-side operations")


class PaginationQuery(BaseModel):
    """Pagination parameters for list queries."""
    
    page: Optional[int] = Field(None, ge=1, description="Page number")
    limit: Optional[int] = Field(None, ge=1, le=100, description="Items per page")
    offset: Optional[int] = Field(None, ge=0, description="Offset for pagination")


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    
    data: list[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class StarknetContract(BaseModel):
    """Starknet contract information."""
    
    contract_address: str
    decimals: int


# Contract mappings for tokens
STARKNET_CONTRACTS: dict[ChainToken, StarknetContract] = {
    ChainToken.USDC: StarknetContract(
        contract_address="0x033068F6539f8e6e6b131e6B2B814e6c34A5224bC66947c47DaB9dFeE93b35fb",
        decimals=6
    ),
    ChainToken.USDC_E: StarknetContract(
        contract_address="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        decimals=6
    ),
    ChainToken.USDT: StarknetContract(
        contract_address="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
        decimals=6
    ),
    ChainToken.DAI: StarknetContract(
        contract_address="0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad",
        decimals=18
    ),
    ChainToken.STRK: StarknetContract(
        contract_address="0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
        decimals=18
    ),
    ChainToken.ETH: StarknetContract(
        contract_address="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        decimals=18
    ),
    ChainToken.WBTC: StarknetContract(
        contract_address="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
        decimals=8
    ),
    ChainToken.OTHER: StarknetContract(
        contract_address="",
        decimals=18
    ),
}
