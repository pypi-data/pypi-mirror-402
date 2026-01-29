"""Constants used across Chipi SDK."""

from .models.wallet import WalletType


# API Versioning
API_VERSION = "1"
API_VERSION_DATE = "2025-12-30"

# Starknet Networks
STARKNET_NETWORKS = {
    "MAINNET": "https://starknet-mainnet.public.blastapi.io/rpc/v0_7",
    "SEPOLIA": "https://starknet-sepolia.public.blastapi.io/rpc/v0_7",
}

# Contract Addresses
CONTRACT_ADDRESSES = {
    "USDC_MAINNET": "0x033068F6539f8e6e6b131e6B2B814e6c34A5224bC66947c47DaB9dFeE93b35fb",
    "VESU_USDC_MAINNET": "0x017f19582c61479f2fe0b6606300e975c0a8f439102f43eeecc1d0e9b3d84350",
}

# Token Decimals
TOKEN_DECIMALS = {
    "USDC": 6,
    "USDT": 6,
    "ETH": 18,
    "STRK": 18,
    "DAI": 18,
    "WBTC": 8,
}

# API Endpoints
API_ENDPOINTS = {
    "CHIPI_WALLETS": "/chipi-wallets",
    "TRANSACTIONS": "/transactions",
    "SKUS": "/skus",
    "SKU_TRANSACTIONS": "/sku-transactions",
    "EXCHANGES": "/exchanges",
    "USERS": "/users",
}

# Default Pagination
DEFAULT_PAGINATION = {
    "PAGE": 1,
    "LIMIT": 10,
    "MAX_LIMIT": 100,
}

# Error Codes
ERRORS = {
    "INVALID_API_KEY": "INVALID_API_KEY",
    "WALLET_NOT_FOUND": "WALLET_NOT_FOUND",
    "INSUFFICIENT_BALANCE": "INSUFFICIENT_BALANCE",
    "TRANSACTION_FAILED": "TRANSACTION_FAILED",
    "INVALID_SIGNATURE": "INVALID_SIGNATURE",
    "SKU_NOT_FOUND": "SKU_NOT_FOUND",
    "SKU_UNAVAILABLE": "SKU_UNAVAILABLE",
}

# SKU Contracts
SKU_CONTRACTS = {
    "RECHARGER_WITH_STRK_MAINNET": "0x02d65bb726d2c29e3c97669cf297c5145eac19284fb6f935c05c0bfc68dae2b7",
    "CHIPI_BILL_SERVICE": "0x4e8150110d580069de26adec9b179023289d55859ea07487aaade5458d7aa8b",
}

# Service Types
SERVICE_TYPES = {
    "BUY_SERVICE": "BUY_SERVICE",
}

# Carrier IDs
CARRIER_IDS = {
    "CHIPI_PAY": "chipi_pay",
}

# Chain Types
CHAIN_TYPES = {
    "STARKNET": "STARKNET",
}

# Chain Token Types
CHAIN_TOKEN_TYPES = {
    "USDC": "USDC",
    "USDT": "USDT",
    "ETH": "ETH",
    "STRK": "STRK",
    "DAI": "DAI",
    "WBTC": "WBTC",
    "OTHER": "OTHER",
}

# Wallet Class Hashes
WALLET_CLASS_HASHES: dict[WalletType, str] = {
    WalletType.CHIPI: "0x2de1565226d5215a38b68c4d9a4913989b54edff64c68c45e453c417b44cd83",
    WalletType.READY: "0x036078334509b514626504edc9fb252328d1a240e4e948bef8d0c08dff45927f",
}

# RPC Endpoints per Wallet Type
WALLET_RPC_ENDPOINTS: dict[WalletType, str] = {
    WalletType.CHIPI: "https://starknet-mainnet.public.blastapi.io/rpc/v0_7",
    WalletType.READY: "https://cloud.argent-api.com/v1/starknet/mainnet/rpc/v0.7",
}

# Paymaster Configuration
PAYMASTER_CONFIG = {
    "URL": "https://paymaster.chipipay.com",
}

# Session Key Configuration (CHIPI wallets only - SNIP-9 compatible)
SESSION_DEFAULTS = {
    "DURATION_SECONDS": 21600,  # Default session duration: 6 hours
    "MAX_CALLS": 1000,  # Default max calls per session
}

# Session-specific Error Codes
SESSION_ERRORS = {
    "INVALID_WALLET_TYPE_FOR_SESSION": "INVALID_WALLET_TYPE_FOR_SESSION",
    "SESSION_EXPIRED": "SESSION_EXPIRED",
    "SESSION_NOT_REGISTERED": "SESSION_NOT_REGISTERED",
    "SESSION_REVOKED": "SESSION_REVOKED",
    "SESSION_MAX_CALLS_EXCEEDED": "SESSION_MAX_CALLS_EXCEEDED",
    "SESSION_ENTRYPOINT_NOT_ALLOWED": "SESSION_ENTRYPOINT_NOT_ALLOWED",
    "SESSION_DECRYPTION_FAILED": "SESSION_DECRYPTION_FAILED",
    "SESSION_CREATION_FAILED": "SESSION_CREATION_FAILED",
}

# Session Contract Entrypoint Names
SESSION_ENTRYPOINTS = {
    "ADD_OR_UPDATE": "add_or_update_session_key",
    "REVOKE": "revoke_session_key",
    "GET_DATA": "get_session_data",
}
