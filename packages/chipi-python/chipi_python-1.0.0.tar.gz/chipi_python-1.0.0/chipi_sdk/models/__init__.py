"""Pydantic models for Chipi SDK."""

# Core types
from .core import (
    Chain,
    ChainToken,
    ChipiSDKConfig,
    PaginatedResponse,
    PaginationQuery,
    StarknetContract,
    STARKNET_CONTRACTS,
)

# Wallet types
from .wallet import (
    CreateCustodialWalletParams,
    CreateWalletParams,
    CreateWalletResponse,
    DeploymentData,
    GetTokenBalanceParams,
    GetTokenBalanceResponse,
    GetWalletParams,
    GetWalletResponse,
    PasskeyMetadata,
    PrepareWalletCreationResponse,
    WalletData,
    WalletType,
)

# Transaction types
from .transaction import (
    ApproveParams,
    Call,
    CallAnyContractParams,
    ExecuteSponsoredTransactionParams,
    ExecuteSponsoredTransactionResponse,
    ExecuteTransactionParams,
    GetTransactionListQuery,
    PrepareTypedDataParams,
    PrepareTypedDataResponse,
    RecordSendTransactionParams,
    StakeVesuUsdcParams,
    Transaction,
    TransferParams,
    WithdrawVesuUsdcParams,
)

# Session types
from .session import (
    AddSessionKeyParams,
    CreateSessionKeyParams,
    ExecuteWithSessionParams,
    GetSessionDataParams,
    RevokeSessionKeyParams,
    SessionConfig,
    SessionDataResponse,
    SessionKeyData,
)

# SKU types
from .sku import (
    GetSkuListQuery,
    Sku,
)

# SKU transaction types
from .sku_transaction import (
    CreateSkuTransactionParams,
    SkuTransaction,
)

# User types
from .user import (
    CreateUserParams,
    GetUserParams,
    User,
)

__all__ = [
    # Core
    "Chain",
    "ChainToken",
    "ChipiSDKConfig",
    "PaginatedResponse",
    "PaginationQuery",
    "StarknetContract",
    "STARKNET_CONTRACTS",
    # Wallet
    "CreateCustodialWalletParams",
    "CreateWalletParams",
    "CreateWalletResponse",
    "DeploymentData",
    "GetTokenBalanceParams",
    "GetTokenBalanceResponse",
    "GetWalletParams",
    "GetWalletResponse",
    "PasskeyMetadata",
    "PrepareWalletCreationResponse",
    "WalletData",
    "WalletType",
    # Transaction
    "ApproveParams",
    "Call",
    "CallAnyContractParams",
    "ExecuteSponsoredTransactionParams",
    "ExecuteSponsoredTransactionResponse",
    "ExecuteTransactionParams",
    "GetTransactionListQuery",
    "PrepareTypedDataParams",
    "PrepareTypedDataResponse",
    "RecordSendTransactionParams",
    "StakeVesuUsdcParams",
    "Transaction",
    "TransferParams",
    "WithdrawVesuUsdcParams",
    # Session
    "AddSessionKeyParams",
    "CreateSessionKeyParams",
    "ExecuteWithSessionParams",
    "GetSessionDataParams",
    "RevokeSessionKeyParams",
    "SessionConfig",
    "SessionDataResponse",
    "SessionKeyData",
    # SKU
    "GetSkuListQuery",
    "Sku",
    # SKU Transaction
    "CreateSkuTransactionParams",
    "SkuTransaction",
    # User
    "CreateUserParams",
    "GetUserParams",
    "User",
]
