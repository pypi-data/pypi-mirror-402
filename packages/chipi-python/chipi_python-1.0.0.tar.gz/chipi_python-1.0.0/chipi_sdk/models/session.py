"""Session key management types and models."""

from typing import Optional
from pydantic import BaseModel, Field

from .transaction import Call
from .wallet import WalletData


class SessionKeyData(BaseModel):
    """Session key information."""
    
    public_key: str = Field(..., description="Session public key")
    encrypted_private_key: str = Field(..., description="AES encrypted session private key")
    valid_until: int = Field(..., description="Unix timestamp when session expires")


class CreateSessionKeyParams(BaseModel):
    """Parameters for creating a session key."""
    
    encrypt_key: str = Field(..., description="Encryption key for session private key")
    duration_seconds: Optional[int] = Field(21600, description="Session duration in seconds (default 6 hours)")


class SessionConfig(BaseModel):
    """Session key configuration for on-chain registration."""
    
    session_public_key: str = Field(..., description="Public key of the session")
    valid_until: int = Field(..., description="Unix timestamp when session expires")
    max_calls: int = Field(..., description="Maximum number of calls allowed")
    allowed_entrypoints: list[str] = Field(..., description="List of allowed contract entrypoints (empty = all allowed)")


class AddSessionKeyParams(BaseModel):
    """Parameters for adding a session key to contract."""
    
    encrypt_key: str = Field(..., description="Encryption key for owner private key")
    wallet: WalletData
    session_config: SessionConfig


class RevokeSessionKeyParams(BaseModel):
    """Parameters for revoking a session key."""
    
    encrypt_key: str = Field(..., description="Encryption key for owner private key")
    wallet: WalletData
    session_public_key: str = Field(..., description="Public key of session to revoke")


class GetSessionDataParams(BaseModel):
    """Parameters for querying session data."""
    
    wallet_address: str = Field(..., description="Wallet contract address")
    session_public_key: str = Field(..., description="Session public key to query")


class SessionDataResponse(BaseModel):
    """Response from session data query."""
    
    is_active: bool = Field(..., description="Whether session is currently active")
    valid_until: int = Field(..., description="Unix timestamp when session expires")
    remaining_calls: int = Field(..., description="Number of calls remaining")
    allowed_entrypoints: list[str] = Field(..., description="List of allowed entrypoints")


class ExecuteWithSessionParams(BaseModel):
    """Parameters for executing transaction with session key."""
    
    encrypt_key: str = Field(..., description="Encryption key for session private key")
    wallet: WalletData
    session: SessionKeyData
    calls: list[Call]
