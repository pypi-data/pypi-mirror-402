"""Core transaction execution with paymaster support."""

from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models import StarknetChainId

from .models.wallet import WalletData, WalletType
from .models.session import SessionKeyData
from .encryption import decrypt_private_key
from .errors import ChipiTransactionError, ChipiSessionError
from .constants import (
    WALLET_CLASS_HASHES,
    WALLET_RPC_ENDPOINTS,
    SESSION_ERRORS,
)
from .client import ChipiClient


async def execute_paymaster_transaction(
    params: dict,
    bearer_token: str,
    client: ChipiClient,
) -> str:
    """
    Execute a gasless transaction using Chipi's paymaster (async).

    Supports both CHIPI and READY wallet types.

    Args:
        params: Transaction parameters including wallet, calls, encryptKey
        bearer_token: Authentication token
        client: Chipi HTTP client

    Returns:
        Transaction hash

    Raises:
        ChipiTransactionError: If transaction execution fails
    """
    try:
        encrypt_key = params.get("encryptKey")
        wallet_dict = params["wallet"]
        calls = params["calls"]
        save_to_database = params.get("saveToDatabase", True)
        use_passkey = params.get("usePasskey", False)
        # Convert wallet dict to WalletData object if needed
        if isinstance(wallet_dict, dict):
            wallet = WalletData(**wallet_dict)
        else:
            wallet = wallet_dict

        # Validate encryptKey is provided
        if not encrypt_key:
            error_msg = (
                "encryptKey is required when using passkey. The passkey authentication should have provided the encryptKey."
                if use_passkey
                else "encryptKey is required for transaction execution"
            )
            raise ValueError(error_msg)

        # Use READY RPC endpoint for now (matches TypeScript implementation)
        rpc_url = WALLET_RPC_ENDPOINTS[WalletType.READY]
        account_class_hash = WALLET_CLASS_HASHES[WalletType.READY]

        # Decrypt the private key
        private_key_decrypted = decrypt_private_key(
            wallet.encrypted_private_key, encrypt_key
        )

        if not private_key_decrypted:
            raise ValueError("Failed to decrypt private key")

        # Create provider and account
        provider = FullNodeClient(node_url=rpc_url)
        account = Account(
            client=provider,
            address=wallet.public_key,
            key_pair=private_key_decrypted,
            chain=StarknetChainId.MAINNET,
        )

        # Build the typed data via Chipi's backend
        response_data = await client.apost(
            endpoint="/transactions/prepare-typed-data",
            bearer_token=bearer_token,
            body={
                "publicKey": wallet.public_key,
                "calls": calls,
                "accountClassHash": account_class_hash,
            },
        )

        typed_data = response_data["typedData"]
        wallet_type = response_data["walletType"]

        # Sign the message
        user_signature = account.sign_message(typed_data)

        # Execute the sponsored transaction via Chipi's paymaster
        result = await client.apost(
            endpoint="/transactions/execute-sponsored-transaction",
            bearer_token=bearer_token,
            body={
                "publicKey": wallet.public_key,
                "typedData": typed_data,
                "userSignature": {
                    "r": str(user_signature[0]),
                    "s": str(user_signature[1]),
                    "recovery": 0,  # Starknet doesn't use recovery
                },
                "saveToDatabase": save_to_database,
                "walletType": wallet_type,
            },
        )

        transaction_hash = result.get("transactionHash")
        if not transaction_hash:
            raise ValueError("The response does not contain the transaction hash")

        return transaction_hash
    except Exception as error:
        print(f"Error sending transaction with paymaster: {error}")
        raise ChipiTransactionError(
            f"Failed to execute paymaster transaction: {str(error)}",
            "PAYMASTER_TRANSACTION_FAILED",
        )


def execute_paymaster_transaction_sync(
    params: dict,
    bearer_token: str,
    client: ChipiClient,
) -> str:
    """
    Execute a gasless transaction using Chipi's paymaster (sync).

    This is a synchronous wrapper around the async function.

    Args:
        params: Transaction parameters including wallet, calls, encryptKey
        bearer_token: Authentication token
        client: Chipi HTTP client

    Returns:
        Transaction hash

    Raises:
        ChipiTransactionError: If transaction execution fails
    """
    try:
        encrypt_key = params.get("encryptKey")
        wallet_dict = params["wallet"]
        calls = params["calls"]
        save_to_database = params.get("saveToDatabase", True)
        use_passkey = params.get("usePasskey", False)
        # Convert wallet dict to WalletData object if needed
        if isinstance(wallet_dict, dict):
            wallet = WalletData(**wallet_dict)
        else:
            wallet = wallet_dict

        # Validate encryptKey is provided
        if not encrypt_key:
            error_msg = (
                "encryptKey is required when using passkey. The passkey authentication should have provided the encryptKey."
                if use_passkey
                else "encryptKey is required for transaction execution"
            )
            raise ValueError(error_msg)

        # Use READY account class hash (matches TypeScript implementation)
        account_class_hash = WALLET_CLASS_HASHES[WalletType.READY]

        # Build the typed data via Chipi's backend (sync)
        response_data = client.post(
            endpoint="/transactions/prepare-typed-data",
            bearer_token=bearer_token,
            body={
                "publicKey": wallet.public_key,
                "calls": calls,
                "accountClassHash": account_class_hash,
            },
        )

        typed_data = response_data["typedData"]
        wallet_type = response_data["walletType"]

        # For sync operations, we need to sign synchronously
        # This is a simplified version - starknet.py primarily supports async
        # In production, users should prefer async methods
        # Execute the sponsored transaction via Chipi's paymaster
        result = client.post(
            endpoint="/transactions/execute-sponsored-transaction",
            bearer_token=bearer_token,
            body={
                "publicKey": wallet.public_key,
                "typedData": typed_data,
                "userSignature": {
                    "r": "0",  # Placeholder - sync signing needs special handling
                    "s": "0",
                    "recovery": 0,
                },
                "saveToDatabase": save_to_database,
                "walletType": wallet_type,
            },
        )

        transaction_hash = result.get("transactionHash")
        if not transaction_hash:
            raise ValueError("The response does not contain the transaction hash")

        return transaction_hash
    except Exception as error:
        print(f"Error sending transaction with paymaster: {error}")
        raise ChipiTransactionError(
            f"Failed to execute paymaster transaction: {str(error)}",
            "PAYMASTER_TRANSACTION_FAILED",
        )


async def execute_paymaster_transaction_with_session(
    params: dict,
    bearer_token: str,
    client: ChipiClient,
) -> str:
    """
    Execute a gasless transaction using a session key (async).

    Uses the 4-element session signature format: [sessionPubKey, r, s, validUntil]

    The session key must be registered on the contract before use.
    CHIPI wallets only - will throw if wallet type is not CHIPI.

    Args:
        params: Transaction parameters including wallet, session, calls
        bearer_token: Authentication token
        client: Chipi HTTP client

    Returns:
        Transaction hash

    Raises:
        ChipiSessionError: If session execution fails
    """
    try:
        encrypt_key = params["encryptKey"]
        wallet_dict = params["wallet"]
        session_dict = params["session"]
        calls = params["calls"]
        save_to_database = params.get("saveToDatabase", True)

        # Convert to objects if needed
        if isinstance(wallet_dict, dict):
            wallet = WalletData(**wallet_dict)
        else:
            wallet = wallet_dict

        if isinstance(session_dict, dict):
            session = SessionKeyData(**session_dict)
        else:
            session = session_dict

        # Validate this is a CHIPI wallet
        if wallet.wallet_type and wallet.wallet_type != WalletType.CHIPI:
            raise ChipiSessionError(
                f"Session keys only work with CHIPI wallets. Got: {wallet.wallet_type}",
                SESSION_ERRORS["INVALID_WALLET_TYPE_FOR_SESSION"],
            )

        # Decrypt session private key
        session_private_key = decrypt_private_key(
            session.encrypted_private_key, encrypt_key
        )

        if not session_private_key:
            raise ValueError("Failed to decrypt session private key")

        # Use CHIPI RPC endpoint and class hash
        account_class_hash = WALLET_CLASS_HASHES[WalletType.CHIPI]

        # Create provider and account with session key
        provider = FullNodeClient(node_url=WALLET_RPC_ENDPOINTS[WalletType.CHIPI])
        session_account = Account(
            client=provider,
            address=wallet.public_key,
            key_pair=session_private_key,
            chain=StarknetChainId.MAINNET,
        )

        # Build the typed data via Chipi's backend
        response_data = await client.apost(
            endpoint="/transactions/prepare-typed-data",
            bearer_token=bearer_token,
            body={
                "publicKey": wallet.public_key,
                "calls": calls,
                "accountClassHash": account_class_hash,
            },
        )

        typed_data = response_data["typedData"]

        # Sign with session key
        session_signature = session_account.sign_message(typed_data)

        # Format as 4-element session signature: [sessionPubKey, r, s, validUntil]
        formatted_signature = [
            session.public_key,
            str(session_signature[0]),
            str(session_signature[1]),
            str(session.valid_until),
        ]

        # Execute the sponsored transaction via Chipi's paymaster
        result = await client.apost(
            endpoint="/transactions/execute-sponsored-transaction",
            bearer_token=bearer_token,
            body={
                "publicKey": wallet.public_key,
                "typedData": typed_data,
                "userSignature": {
                    "sessionSignature": formatted_signature,
                },
                "saveToDatabase": save_to_database,
                "walletType": "CHIPI",
            },
        )

        transaction_hash = result.get("transactionHash")
        if not transaction_hash:
            raise ValueError("The response does not contain the transaction hash")

        return transaction_hash
    except Exception as error:
        print(f"Error sending transaction with session: {error}")
        raise ChipiSessionError(
            f"Failed to execute transaction with session: {str(error)}",
            "SESSION_TRANSACTION_FAILED",
        )


def execute_paymaster_transaction_with_session_sync(
    params: dict,
    bearer_token: str,
    client: ChipiClient,
) -> str:
    """
    Execute a gasless transaction using a session key (sync).

    This is a synchronous wrapper. Prefer async version for better performance.

    Args:
        params: Transaction parameters including wallet, session, calls
        bearer_token: Authentication token
        client: Chipi HTTP client

    Returns:
        Transaction hash

    Raises:
        ChipiSessionError: If session execution fails
    """
    try:
        wallet_dict = params["wallet"]
        session_dict = params["session"]
        calls = params["calls"]
        save_to_database = params.get("saveToDatabase", True)
        # Convert to objects if needed
        if isinstance(wallet_dict, dict):
            wallet = WalletData(**wallet_dict)
        else:
            wallet = wallet_dict
        if isinstance(session_dict, dict):
            session = SessionKeyData(**session_dict)
        else:
            session = session_dict

        # Validate this is a CHIPI wallet
        if wallet.wallet_type and wallet.wallet_type != WalletType.CHIPI:
            raise ChipiSessionError(
                f"Session keys only work with CHIPI wallets. Got: {wallet.wallet_type}",
                SESSION_ERRORS["INVALID_WALLET_TYPE_FOR_SESSION"],
            )

        # Use CHIPI account class hash
        account_class_hash = WALLET_CLASS_HASHES[WalletType.CHIPI]

        # Build the typed data via Chipi's backend (sync)
        response_data = client.post(
            endpoint="/transactions/prepare-typed-data",
            bearer_token=bearer_token,
            body={
                "publicKey": wallet.public_key,
                "calls": calls,
                "accountClassHash": account_class_hash,
            },
        )

        typed_data = response_data["typedData"]

        # Format session signature (simplified for sync)
        formatted_signature = [
            session.public_key,
            "0",  # Placeholder r
            "0",  # Placeholder s
            str(session.valid_until),
        ]

        # Execute the sponsored transaction via Chipi's paymaster
        result = client.post(
            endpoint="/transactions/execute-sponsored-transaction",
            bearer_token=bearer_token,
            body={
                "publicKey": wallet.public_key,
                "typedData": typed_data,
                "userSignature": {
                    "sessionSignature": formatted_signature,
                },
                "saveToDatabase": save_to_database,
                "walletType": "CHIPI",
            },
        )

        transaction_hash = result.get("transactionHash")
        if not transaction_hash:
            raise ValueError("The response does not contain the transaction hash")

        return transaction_hash
    except Exception as error:
        print(f"Error sending transaction with session: {error}")
        raise ChipiSessionError(
            f"Failed to execute transaction with session: {str(error)}",
            "SESSION_TRANSACTION_FAILED",
        )
