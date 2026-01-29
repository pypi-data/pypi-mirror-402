"""Wallet-related types and models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from .core import Chain, ChainToken


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class WalletType(str, Enum):
    """
    Supported wallet types.
    
    - CHIPI: OpenZeppelin account with SNIP-9 session keys support (default)
    - READY: Argent X Account v0.4.0
    """
    CHIPI = "CHIPI"
    READY = "READY"


class WalletData(BaseModel):
    """Core wallet data structure."""
    
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    public_key: str = Field(..., description="Wallet public address")
    encrypted_private_key: str = Field(..., description="AES encrypted private key")
    wallet_type: Optional[WalletType] = Field(None, description="Type of wallet")
    normalized_public_key: Optional[str] = Field(None, description="Normalized public key")


class DeploymentData(BaseModel):
    """Contract deployment data."""
    
    class_hash: str
    salt: str
    unique: str
    calldata: list[str]


class CreateWalletParams(BaseModel):
    """Parameters for creating a new wallet."""
    
    encrypt_key: Optional[str] = Field(None, description="Encryption key for private key")
    external_user_id: str = Field(..., description="External user identifier")
    user_id: Optional[str] = Field(None, description="Internal user ID")
    wallet_type: Optional[WalletType] = Field(WalletType.CHIPI, description="Type of wallet to create")
    use_passkey: Optional[bool] = Field(False, description="Whether to use passkey authentication")


class CreateWalletResponse(BaseModel):
    """Response from wallet creation."""
    
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    tx_hash: str = Field(..., description="Transaction hash for wallet deployment")
    wallet_public_key: str = Field(..., description="Public key of created wallet")
    wallet: WalletData = Field(..., description="Wallet data")


class GetWalletParams(BaseModel):
    """Parameters for retrieving a wallet."""
    
    external_user_id: str = Field(..., description="External user identifier")


class GetTokenBalanceParams(BaseModel):
    """Parameters for querying token balance."""
    
    external_user_id: Optional[str] = Field(None, description="External user identifier")
    wallet_public_key: Optional[str] = Field(None, description="Wallet public key")
    chain_token: ChainToken = Field(..., description="Token to query")
    chain: Chain = Field(..., description="Blockchain network")


class GetTokenBalanceResponse(BaseModel):
    """Response from token balance query."""
    
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    chain: Chain
    chain_token: ChainToken
    chain_token_address: str
    decimals: int
    balance: str


class GetWalletResponse(BaseModel):
    """Response from wallet retrieval."""
    
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    id: str
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    wallet: WalletData
    external_user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PrepareWalletCreationResponse(BaseModel):
    """Response from wallet creation preparation."""
    
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    typed_data: dict
    account_class_hash: str


class CreateCustodialWalletParams(BaseModel):
    """Parameters for creating a custodial wallet."""
    
    chain: Chain
    org_id: str


class PasskeyMetadata(BaseModel):
    """Passkey authentication metadata."""
    
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    
    credential_id: str
    created_at: str
    user_id: str
    prf_supported: bool
