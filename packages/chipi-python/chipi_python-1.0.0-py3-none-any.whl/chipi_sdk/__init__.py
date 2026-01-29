"""
Chipi Python SDK for Starknet Gasless Transactions.

A Python SDK for interacting with Chipi's gasless transaction infrastructure on Starknet.
Supports wallet creation, transaction execution, session keys, and more.
"""

__version__ = "1.0.0"

# Main SDK class
from .sdk import ChipiSDK

# Client
from .client import ChipiClient

# Service managers
from .wallets import ChipiWallets
from .transactions import ChipiTransactions
from .sessions import ChipiSessions
from .skus import ChipiSkus
from .sku_transactions import ChipiSkuTransactions
from .users import ChipiUsers

# Models - Core
from .models.core import (
    Chain,
    ChainToken,
    ChipiSDKConfig,
    PaginatedResponse,
    PaginationQuery,
    StarknetContract,
    STARKNET_CONTRACTS,
)

# Models - Wallet
from .models.wallet import (
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

# Models - Transaction
from .models.transaction import (
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

# Models - Session
from .models.session import (
    AddSessionKeyParams,
    CreateSessionKeyParams,
    ExecuteWithSessionParams,
    GetSessionDataParams,
    RevokeSessionKeyParams,
    SessionConfig,
    SessionDataResponse,
    SessionKeyData,
)

# Models - SKU
from .models.sku import (
    GetSkuListQuery,
    Sku,
)

# Models - SKU Transaction
from .models.sku_transaction import (
    CreateSkuTransactionParams,
    SkuTransaction,
)

# Models - User
from .models.user import (
    CreateUserParams,
    GetUserParams,
    User,
)

# Errors
from .errors import (
    ChipiApiError,
    ChipiAuthError,
    ChipiError,
    ChipiSessionError,
    ChipiSkuError,
    ChipiTransactionError,
    ChipiValidationError,
    ChipiWalletError,
    handle_api_error,
    is_chipi_error,
)

# Constants
from .constants import (
    API_ENDPOINTS,
    API_VERSION,
    API_VERSION_DATE,
    CARRIER_IDS,
    CHAIN_TOKEN_TYPES,
    CHAIN_TYPES,
    CONTRACT_ADDRESSES,
    DEFAULT_PAGINATION,
    ERRORS,
    PAYMASTER_CONFIG,
    SERVICE_TYPES,
    SESSION_DEFAULTS,
    SESSION_ENTRYPOINTS,
    SESSION_ERRORS,
    SKU_CONTRACTS,
    STARKNET_NETWORKS,
    TOKEN_DECIMALS,
    WALLET_CLASS_HASHES,
    WALLET_RPC_ENDPOINTS,
)

# Utilities
from .formatters import (
    camel_to_snake,
    capitalize_first,
    format_address,
    format_amount,
    format_currency,
    format_number,
    format_transaction_hash,
    snake_to_camel,
)

from .validators import (
    is_valid_api_key,
    validate_address,
    validate_error_response,
)

from .encryption import (
    decrypt_private_key,
    encrypt_private_key,
)

__all__ = [
    # Version
    "__version__",
    # Main SDK
    "ChipiSDK",
    # Client
    "ChipiClient",
    # Service managers
    "ChipiWallets",
    "ChipiTransactions",
    "ChipiSessions",
    "ChipiSkus",
    "ChipiSkuTransactions",
    "ChipiUsers",
    # Core models
    "Chain",
    "ChainToken",
    "ChipiSDKConfig",
    "PaginatedResponse",
    "PaginationQuery",
    "StarknetContract",
    "STARKNET_CONTRACTS",
    # Wallet models
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
    # Transaction models
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
    # Session models
    "AddSessionKeyParams",
    "CreateSessionKeyParams",
    "ExecuteWithSessionParams",
    "GetSessionDataParams",
    "RevokeSessionKeyParams",
    "SessionConfig",
    "SessionDataResponse",
    "SessionKeyData",
    # SKU models
    "GetSkuListQuery",
    "Sku",
    # SKU Transaction models
    "CreateSkuTransactionParams",
    "SkuTransaction",
    # User models
    "CreateUserParams",
    "GetUserParams",
    "User",
    # Errors
    "ChipiApiError",
    "ChipiAuthError",
    "ChipiError",
    "ChipiSessionError",
    "ChipiSkuError",
    "ChipiTransactionError",
    "ChipiValidationError",
    "ChipiWalletError",
    "handle_api_error",
    "is_chipi_error",
    # Constants
    "API_ENDPOINTS",
    "API_VERSION",
    "API_VERSION_DATE",
    "CARRIER_IDS",
    "CHAIN_TOKEN_TYPES",
    "CHAIN_TYPES",
    "CONTRACT_ADDRESSES",
    "DEFAULT_PAGINATION",
    "ERRORS",
    "PAYMASTER_CONFIG",
    "SERVICE_TYPES",
    "SESSION_DEFAULTS",
    "SESSION_ENTRYPOINTS",
    "SESSION_ERRORS",
    "SKU_CONTRACTS",
    "STARKNET_NETWORKS",
    "TOKEN_DECIMALS",
    "WALLET_CLASS_HASHES",
    "WALLET_RPC_ENDPOINTS",
    # Utilities
    "camel_to_snake",
    "capitalize_first",
    "format_address",
    "format_amount",
    "format_currency",
    "format_number",
    "format_transaction_hash",
    "snake_to_camel",
    "is_valid_api_key",
    "validate_address",
    "validate_error_response",
    "decrypt_private_key",
    "encrypt_private_key",
]
