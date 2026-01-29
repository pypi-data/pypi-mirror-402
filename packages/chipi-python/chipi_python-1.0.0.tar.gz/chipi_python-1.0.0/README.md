# Chipi Python SDK

[![PyPI version](https://badge.fury.io/py/chipi-python.svg)](https://badge.fury.io/py/chipi-python)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python SDK for executing gasless transactions on Starknet via Chipi's paymaster infrastructure.

## Features

- 🚀 **Gasless Transactions** - Execute transactions without paying gas fees
- 💼 **Wallet Management** - Create and manage Starknet wallets
- 🔐 **Session Keys** - SNIP-9 compatible session key support for CHIPI wallets
- 🔄 **Sync & Async** - Full support for both synchronous and asynchronous operations
- 📦 **Type Safe** - Built with Pydantic for runtime validation and type safety
- 🎯 **Simple API** - Easy-to-use interface for all operations

## Installation

```bash
pip install chipi-python
```

Or with uv:

```bash
uv add chipi-python
```

### Requirements

- Python 3.11 or higher
- Dependencies:
  - `starknet-py>=0.23.0` - Starknet interactions
  - `pydantic>=2.0.0` - Data validation
  - `httpx>=0.27.0` - HTTP client
  - `cryptography>=42.0.0` - AES encryption

## Quick Start

### Initialize the SDK

```python
from chipi_sdk import ChipiSDK, ChipiSDKConfig

# Initialize SDK with your API keys
sdk = ChipiSDK(
    config=ChipiSDKConfig(
        api_public_key="your_public_key",
        api_secret_key="your_secret_key",  # Optional for server-side
    )
)
```

### Create a Wallet

```python
from chipi_sdk import CreateWalletParams, WalletType

# Synchronous
wallet_response = sdk.create_wallet(
    params=CreateWalletParams(
        encrypt_key="user_password",
        external_user_id="user123",
        wallet_type=WalletType.CHIPI,
    )
)

print(f"Wallet created: {wallet_response.wallet_public_key}")
print(f"Transaction hash: {wallet_response.tx_hash}")

# Async version
wallet_response = await sdk.acreate_wallet(params=params)
```

### Execute a Gasless Transaction

```python
from chipi_sdk import ExecuteTransactionParams, Call

# Transfer tokens without gas fees
tx_hash = sdk.execute_transaction(
    params=ExecuteTransactionParams(
        encrypt_key="user_password",
        wallet=wallet_data,
        calls=[
            Call(
                contractAddress="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
                entrypoint="transfer",
                calldata=[recipient_address, amount, "0x0"],
            )
        ],
    )
)

print(f"Transaction executed: {tx_hash}")
```

### Transfer Tokens (Convenience Method)

```python
from chipi_sdk import TransferParams, ChainToken

tx_hash = sdk.transfer(
    params=TransferParams(
        encrypt_key="user_password",
        wallet=wallet_data,
        token=ChainToken.USDC,
        recipient="0x...",
        amount="1.5",  # Human-readable amount
    )
)
```

### Session Keys (CHIPI Wallets Only)

```python
from chipi_sdk import CreateSessionKeyParams, SessionConfig, AddSessionKeyParams

# 1. Create session key locally
session = sdk.sessions.create_session_key(
    params=CreateSessionKeyParams(
        encrypt_key="user_password",
        duration_seconds=21600,  # 6 hours
    )
)

# 2. Register session on-chain (one-time)
tx_hash = await sdk.sessions.aadd_session_key_to_contract(
    params=AddSessionKeyParams(
        encrypt_key="user_password",
        wallet=wallet_data,
        session_config=SessionConfig(
            session_public_key=session.public_key,
            valid_until=session.valid_until,
            max_calls=1000,
            allowed_entrypoints=[],  # Empty = all allowed
        ),
    ),
    bearer_token="your_token",
)

# 3. Execute transactions with session (no owner key needed!)
from chipi_sdk import ExecuteWithSessionParams

tx_hash = await sdk.aexecute_transaction_with_session(
    params=ExecuteWithSessionParams(
        encrypt_key="user_password",
        wallet=wallet_data,
        session=session,
        calls=[...],
    )
)
```

## Async/Await Support

Every method has both sync and async versions:

```python
# Synchronous
wallet = sdk.get_wallet(params=params, bearer_token="token")
tx_hash = sdk.transfer(params=transfer_params)

# Asynchronous (prefix with 'a')
wallet = await sdk.aget_wallet(params=params, bearer_token="token")
tx_hash = await sdk.atransfer(params=transfer_params)
```

## API Reference

### Main SDK Class

- `ChipiSDK` - Main SDK class with all operations

### Wallet Operations

- `create_wallet()` / `acreate_wallet()` - Create new wallet
- `get_wallet()` / `aget_wallet()` - Retrieve wallet by user ID
- `get_token_balance()` / `aget_token_balance()` - Query token balances

### Transaction Operations

- `execute_transaction()` / `aexecute_transaction()` - Execute custom calls
- `transfer()` / `atransfer()` - Transfer tokens
- `approve()` / `aapprove()` - Approve token spending
- `stake_vesu_usdc()` / `astake_vesu_usdc()` - Stake in Vesu protocol
- `withdraw_vesu_usdc()` / `awithdraw_vesu_usdc()` - Withdraw from Vesu
- `get_transaction_list()` / `aget_transaction_list()` - Query transaction history

### Session Key Operations (CHIPI Wallets)

- `create_session_key()` - Generate session keypair locally
- `add_session_key_to_contract()` / `aadd_session_key_to_contract()` - Register session
- `revoke_session_key()` / `arevoke_session_key()` - Revoke session
- `get_session_data()` / `aget_session_data()` - Query session status
- `execute_transaction_with_session()` / `aexecute_transaction_with_session()` - Execute with session

### User Operations

- `create_user()` / `acreate_user()` - Create user
- `get_user()` / `aget_user()` - Get user by external ID

### SKU Operations

- `get_sku_list()` / `aget_sku_list()` - List SKUs
- `get_sku()` / `aget_sku()` - Get SKU by ID
- `create_sku_transaction()` / `acreate_sku_transaction()` - Create SKU transaction

## Error Handling

```python
from chipi_sdk import (
    ChipiError,
    ChipiApiError,
    ChipiWalletError,
    ChipiTransactionError,
    ChipiSessionError,
)

try:
    tx_hash = sdk.execute_transaction(params=params)
except ChipiTransactionError as e:
    print(f"Transaction failed: {e.message}")
    print(f"Error code: {e.code}")
except ChipiApiError as e:
    print(f"API error: {e.message} (status: {e.status})")
except ChipiError as e:
    print(f"General error: {e.message}")
```

## Configuration

### SDK Config Options

```python
from chipi_sdk import ChipiSDKConfig

config = ChipiSDKConfig(
    api_public_key="your_public_key",       # Required
    api_secret_key="your_secret_key",       # Optional - for server-side
    alpha_url="https://custom-api.com",     # Optional - custom API URL
    node_url="https://custom-rpc.com",      # Optional - custom Starknet RPC
)
```

### Wallet Types

- `WalletType.CHIPI` - OpenZeppelin account with SNIP-9 session keys (default)
- `WalletType.READY` - Argent X Account v0.4.0

### Supported Tokens

- USDC (Native)
- USDC_E (Bridged)
- USDT
- ETH
- STRK
- DAI
- WBTC
- OTHER (custom tokens)

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/chipi-pay/chipi-sdk.git
cd chipi-sdk/python

# Install with dev dependencies
pip install -e ".[dev]"

# Or with uv
uv pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

### Format Code

```bash
black chipi_sdk/
ruff check chipi_sdk/ --fix
```

### Type Checking

```bash
mypy chipi_sdk/
```

## Examples

See the [examples](https://github.com/chipi-pay/chipi-sdk/tree/main/python/examples) directory for more usage examples.

## Related SDKs

- [TypeScript SDK](https://www.npmjs.com/package/@chipi-stack/backend) - For Node.js/TypeScript projects
- [React SDK](https://www.npmjs.com/package/@chipi-stack/react) - For React applications

## Documentation

Full documentation is available at [docs.chipipay.com](https://docs.chipipay.com)

## Support

- 📧 Email: support@chipipay.com
- 💬 Discord: [Starknet Discord](https://discord.gg/starknet) (#chipi channel)
- 🐛 Issues: [GitHub Issues](https://github.com/chipi-pay/chipi-sdk/issues)

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

---

Built with ❤️ by the Chipi team
