"""Transaction-related types and models."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict

from .core import Chain, ChainToken
from .wallet import WalletData


class Call(BaseModel):
    """Starknet contract call structure."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    contract_address: str = Field(..., alias="contractAddress")
    entrypoint: str
    calldata: list[str]


class ExecuteTransactionParams(BaseModel):
    """Parameters for executing a transaction."""
    
    encrypt_key: Optional[str] = Field(None, description="Encryption key for private key")
    wallet: WalletData
    calls: list[Call]
    use_passkey: Optional[bool] = Field(False, description="Whether to use passkey authentication")


class TransferParams(BaseModel):
    """Parameters for token transfer."""
    
    encrypt_key: Optional[str] = Field(None, description="Encryption key for private key")
    wallet: WalletData
    token: ChainToken
    other_token: Optional[dict[str, Any]] = Field(None, description="Custom token info for OTHER type")
    recipient: str
    amount: str
    use_passkey: Optional[bool] = Field(False, description="Whether to use passkey authentication")


class ApproveParams(BaseModel):
    """Parameters for token approval."""
    
    encrypt_key: Optional[str] = Field(None, description="Encryption key for private key")
    wallet: WalletData
    contract_address: str
    spender: str
    amount: str
    decimals: Optional[int] = Field(18, description="Token decimals")
    use_passkey: Optional[bool] = Field(False, description="Whether to use passkey authentication")


class CallAnyContractParams(BaseModel):
    """Parameters for calling any contract."""
    
    encrypt_key: Optional[str] = Field(None, description="Encryption key for private key")
    wallet: WalletData
    contract_address: str
    calls: list[Call]
    use_passkey: Optional[bool] = Field(False, description="Whether to use passkey authentication")


class StakeVesuUsdcParams(BaseModel):
    """Parameters for staking USDC in Vesu protocol."""
    
    encrypt_key: Optional[str] = Field(None, description="Encryption key for private key")
    wallet: WalletData
    amount: str
    receiver_wallet: str


class WithdrawVesuUsdcParams(BaseModel):
    """Parameters for withdrawing USDC from Vesu protocol."""
    
    encrypt_key: Optional[str] = Field(None, description="Encryption key for private key")
    wallet: WalletData
    amount: str
    recipient: str


class RecordSendTransactionParams(BaseModel):
    """Parameters for recording a send transaction."""
    
    transaction_hash: str
    expected_sender: str
    expected_recipient: str
    expected_token: ChainToken
    expected_amount: str
    chain: Chain


class Transaction(BaseModel):
    """Transaction record."""
    
    id: str
    chain: str
    api_public_key: str
    transaction_hash: str
    block_number: int
    sender_address: str
    destination_address: str
    amount: str
    token: str
    called_function: Optional[str] = None
    amount_in_usd: float = Field(..., alias="amountInUSD")
    status: str
    is_chipi_wallet: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class PrepareTypedDataParams(BaseModel):
    """Parameters for preparing typed data."""
    
    calls: list[Call]
    wallet_address: str


class PrepareTypedDataResponse(BaseModel):
    """Response from typed data preparation."""
    
    typed_data: dict
    wallet_type: str


class ExecuteSponsoredTransactionParams(BaseModel):
    """Parameters for executing sponsored transaction."""
    
    calls: list[Call]
    wallet_address: str
    signature: list[str]
    api_public_key: str


class ExecuteSponsoredTransactionResponse(BaseModel):
    """Response from sponsored transaction execution."""
    
    transaction_hash: str


class GetTransactionListQuery(BaseModel):
    """Query parameters for transaction list."""
    
    page: Optional[int] = Field(None, ge=1)
    limit: Optional[int] = Field(None, ge=1, le=100)
    called_function: Optional[str] = None
    wallet_address: str = Field(..., description="Wallet address to filter transactions")
    day: Optional[int] = Field(None, ge=1, le=31, description="Day of the month")
    month: Optional[int] = Field(None, ge=1, le=12, description="Month of the year")
    year: Optional[int] = Field(None, description="Year")
