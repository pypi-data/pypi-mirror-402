"""Session key management for CHIPI wallets (SNIP-9 compatible)."""

import time
import secrets
from typing import Optional
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair

from .models.session import (
    SessionKeyData,
    CreateSessionKeyParams,
    AddSessionKeyParams,
    RevokeSessionKeyParams,
    GetSessionDataParams,
    SessionDataResponse,
    ExecuteWithSessionParams,
)
from .models.wallet import WalletType
from .encryption import encrypt_private_key
from .errors import ChipiSessionError
from .constants import (
    WALLET_CLASS_HASHES,
    WALLET_RPC_ENDPOINTS,
    SESSION_DEFAULTS,
    SESSION_ERRORS,
    SESSION_ENTRYPOINTS,
)
from .client import ChipiClient
from .execute_paymaster import (
    execute_paymaster_transaction,
    execute_paymaster_transaction_sync,
    execute_paymaster_transaction_with_session,
    execute_paymaster_transaction_with_session_sync,
)


class ChipiSessions:
    """Session key management for CHIPI wallets."""

    def __init__(self, client: ChipiClient):
        """
        Initialize session manager.

        Args:
            client: Chipi HTTP client
        """
        self.client = client

    def _validate_chipi_wallet(
        self,
        wallet_type: Optional[WalletType],
        operation: str,
        wallet_public_key: Optional[str] = None,
    ) -> None:
        """
        Validate that the wallet is a CHIPI wallet.

        Args:
            wallet_type: Wallet type
            operation: Operation name for error messages
            wallet_public_key: Optional wallet address for logging

        Raises:
            ChipiSessionError: If wallet type is not CHIPI
        """
        if wallet_type != WalletType.CHIPI:
            print(
                f"[ChipiSDK:Session:{operation}] Invalid wallet type",
                {
                    "provided": wallet_type,
                    "required": "CHIPI",
                    "expectedClassHash": WALLET_CLASS_HASHES[WalletType.CHIPI],
                    "walletAddress": (
                        wallet_public_key[:15] + "..." if wallet_public_key else "(not provided)"
                    ),
                    "hint": "Session keys only work with CHIPI wallets (SNIP-9 compatible)",
                },
            )
            raise ChipiSessionError(
                f"Session keys require CHIPI wallet type. Got: \"{wallet_type or 'undefined'}\". "
                f"Session keys are only supported for CHIPI wallets with class hash {WALLET_CLASS_HASHES[WalletType.CHIPI]}",
                SESSION_ERRORS["INVALID_WALLET_TYPE_FOR_SESSION"],
            )

    def _to_hex(self, data: bytes) -> str:
        """
        Convert bytes to hex string with 0x prefix.

        Args:
            data: Bytes to convert

        Returns:
            Hex string with 0x prefix
        """
        return "0x" + data.hex()

    def create_session_key(self, params: CreateSessionKeyParams) -> SessionKeyData:
        """
        Generate a new session keypair locally.

        This method generates the session keys but does NOT register them on-chain.
        The returned SessionKeyData should be stored externally by the developer.

        After generating, call `add_session_key_to_contract()` to register on-chain.

        Args:
            params: Session creation parameters

        Returns:
            Session key data for external storage

        Raises:
            ChipiSessionError: If session creation fails
        """
        encrypt_key = params.encrypt_key
        duration_seconds = params.duration_seconds or SESSION_DEFAULTS["DURATION_SECONDS"]

        try:
            # Generate random private key (32 bytes)
            raw_private_key = secrets.token_bytes(32)
            private_key_hex = self._to_hex(raw_private_key)

            # Derive public key using starknet.py
            key_pair = KeyPair.from_private_key(int(private_key_hex, 16))
            public_key = hex(key_pair.public_key)

            # Calculate expiration timestamp
            valid_until = int(time.time()) + duration_seconds

            # Encrypt the private key for storage
            encrypted_private_key = encrypt_private_key(private_key_hex, encrypt_key)

            return SessionKeyData(
                public_key=public_key,
                encrypted_private_key=encrypted_private_key,
                valid_until=valid_until,
            )
        except Exception as error:
            raise ChipiSessionError(
                f"Failed to create session key: {str(error)}",
                SESSION_ERRORS["SESSION_CREATION_FAILED"],
            )

    async def aadd_session_key_to_contract(
        self, params: AddSessionKeyParams, bearer_token: str
    ) -> str:
        """
        Register a session key on the smart contract (async).

        Executes a sponsored transaction to call `add_or_update_session_key`.
        The session must be registered before it can be used for transactions.

        Args:
            params: Session registration parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash

        Raises:
            ChipiSessionError: If registration fails
        """
        encrypt_key = params.encrypt_key
        wallet = params.wallet
        session_config = params.session_config

        # Validate CHIPI wallet
        self._validate_chipi_wallet(
            wallet.wallet_type, "AddToContract", wallet.public_key
        )

        try:
            print(
                "[ChipiSDK:Session:AddToContract] Registering session on-chain",
                {
                    "walletAddress": wallet.public_key[:15] + "...",
                    "sessionPubKey": session_config.session_public_key[:15] + "...",
                    "validUntil": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.gmtime(session_config.valid_until)
                    ),
                    "maxCalls": session_config.max_calls,
                    "allowedEntrypoints": len(session_config.allowed_entrypoints),
                },
            )

            # Build calldata for add_or_update_session_key
            calldata = [
                session_config.session_public_key,
                hex(session_config.valid_until),
                hex(session_config.max_calls),
                hex(len(session_config.allowed_entrypoints)),
                *session_config.allowed_entrypoints,
            ]

            # Execute via paymaster (owner signature)
            from .models.transaction import Call

            tx_hash = await execute_paymaster_transaction(
                params={
                    "encryptKey": encrypt_key,
                    "wallet": {**wallet.model_dump(), "walletType": "CHIPI"},
                    "calls": [
                        Call(
                            contractAddress=wallet.public_key,
                            entrypoint=SESSION_ENTRYPOINTS["ADD_OR_UPDATE"],
                            calldata=calldata,
                        ).model_dump()
                    ],
                    "saveToDatabase": False,  # Don't record session management txs
                },
                bearer_token=bearer_token,
                client=self.client,
            )

            print(
                "[ChipiSDK:Session:AddToContract] Session registered successfully",
                {
                    "txHash": tx_hash,
                    "sessionPubKey": session_config.session_public_key[:15] + "...",
                },
            )

            return tx_hash
        except Exception as error:
            print(
                "[ChipiSDK:Session:AddToContract] Registration failed",
                {"error": str(error)},
            )
            raise

    def add_session_key_to_contract(
        self, params: AddSessionKeyParams, bearer_token: str
    ) -> str:
        """
        Register a session key on the smart contract (sync).

        Args:
            params: Session registration parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash
        """
        import asyncio
        return asyncio.run(self.aadd_session_key_to_contract(params, bearer_token))

    async def arevoke_session_key(
        self, params: RevokeSessionKeyParams, bearer_token: str
    ) -> str:
        """
        Revoke a session key from the smart contract (async).

        After revocation, the session key can no longer be used for transactions.

        Args:
            params: Session revocation parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash
        """
        encrypt_key = params.encrypt_key
        wallet = params.wallet
        session_public_key = params.session_public_key

        # Validate CHIPI wallet
        self._validate_chipi_wallet(wallet.wallet_type, "Revoke", wallet.public_key)

        try:
            print(
                "[ChipiSDK:Session:Revoke] Revoking session from contract",
                {
                    "walletAddress": wallet.public_key[:15] + "...",
                    "sessionToRevoke": session_public_key[:15] + "...",
                },
            )

            # Execute via paymaster (owner signature)
            from .models.transaction import Call

            tx_hash = await execute_paymaster_transaction(
                params={
                    "encryptKey": encrypt_key,
                    "wallet": {**wallet.model_dump(), "walletType": "CHIPI"},
                    "calls": [
                        Call(
                            contractAddress=wallet.public_key,
                            entrypoint=SESSION_ENTRYPOINTS["REVOKE"],
                            calldata=[session_public_key],
                        ).model_dump()
                    ],
                    "saveToDatabase": False,
                },
                bearer_token=bearer_token,
                client=self.client,
            )

            print(
                "[ChipiSDK:Session:Revoke] Session revoked successfully",
                {
                    "txHash": tx_hash,
                    "sessionRevoked": session_public_key[:15] + "...",
                },
            )

            return tx_hash
        except Exception as error:
            print("[ChipiSDK:Session:Revoke] Revocation failed", {"error": str(error)})
            raise

    def revoke_session_key(
        self, params: RevokeSessionKeyParams, bearer_token: str
    ) -> str:
        """
        Revoke a session key from the smart contract (sync).

        Args:
            params: Session revocation parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash
        """
        import asyncio
        return asyncio.run(self.arevoke_session_key(params, bearer_token))

    async def aget_session_data(
        self, params: GetSessionDataParams
    ) -> SessionDataResponse:
        """
        Query session data from the smart contract (async).

        This is a read-only call that does not require signing or gas.

        Args:
            params: Query parameters

        Returns:
            Session data including status and remaining calls
        """
        wallet_address = params.wallet_address
        session_public_key = params.session_public_key

        try:
            provider = FullNodeClient(node_url=WALLET_RPC_ENDPOINTS[WalletType.CHIPI])

            print(
                "[ChipiSDK:Session:GetData] Querying session data",
                {
                    "walletAddress": wallet_address[:15] + "...",
                    "sessionPubKey": session_public_key[:15] + "...",
                },
            )

            result = await provider.call_contract(
                call={
                    "contract_address": int(wallet_address, 16),
                    "entry_point_selector": get_selector_from_name(
                        SESSION_ENTRYPOINTS["GET_DATA"]
                    ),
                    "calldata": [int(session_public_key, 16)],
                }
            )

            # Parse the response
            if len(result) < 4:
                print(
                    "[ChipiSDK:Session:GetData] Unexpected response format",
                    {"resultLength": len(result)},
                )
                return SessionDataResponse(
                    is_active=False,
                    valid_until=0,
                    remaining_calls=0,
                    allowed_entrypoints=[],
                )

            is_active = result[0] == 1
            valid_until = int(result[1])
            remaining_calls = int(result[2])
            entrypoints_len = int(result[3])
            allowed_entrypoints = [hex(val) for val in result[4 : 4 + entrypoints_len]]

            session_data = SessionDataResponse(
                is_active=is_active,
                valid_until=valid_until,
                remaining_calls=remaining_calls,
                allowed_entrypoints=allowed_entrypoints,
            )

            print(
                "[ChipiSDK:Session:GetData] Session data retrieved",
                {
                    "isActive": is_active,
                    "validUntil": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.gmtime(valid_until)
                    ),
                    "remainingCalls": remaining_calls,
                    "allowedEntrypointsCount": len(allowed_entrypoints),
                },
            )

            return session_data
        except Exception as error:
            print(
                "[ChipiSDK:Session:GetData] Query failed", {"error": str(error)}
            )
            # Return inactive session on error
            return SessionDataResponse(
                is_active=False,
                valid_until=0,
                remaining_calls=0,
                allowed_entrypoints=[],
            )

    def get_session_data(self, params: GetSessionDataParams) -> SessionDataResponse:
        """
        Query session data from the smart contract (sync).

        Args:
            params: Query parameters

        Returns:
            Session data
        """
        import asyncio
        return asyncio.run(self.aget_session_data(params))

    async def aexecute_transaction_with_session(
        self, params: ExecuteWithSessionParams, bearer_token: str
    ) -> str:
        """
        Execute a gasless transaction using a session key (async).

        The session must be registered on-chain before use.
        CHIPI wallets only.

        Args:
            params: Session execution parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash
        """
        # Validate wallet type if provided
        if params.wallet.wallet_type and params.wallet.wallet_type != WalletType.CHIPI:
            raise ChipiSessionError(
                f"Session execution only supports CHIPI wallets. Got: {params.wallet.wallet_type}",
                SESSION_ERRORS["INVALID_WALLET_TYPE_FOR_SESSION"],
            )

        return await execute_paymaster_transaction_with_session(
            params={
                "encryptKey": params.encrypt_key,
                "wallet": {**params.wallet.model_dump(), "walletType": "CHIPI"},
                "session": params.session.model_dump(),
                "calls": [call.model_dump() for call in params.calls],
                "saveToDatabase": True,
            },
            bearer_token=bearer_token,
            client=self.client,
        )

    def execute_transaction_with_session(
        self, params: ExecuteWithSessionParams, bearer_token: str
    ) -> str:
        """
        Execute a gasless transaction using a session key (sync).

        Args:
            params: Session execution parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash
        """
        # Validate wallet type if provided
        if params.wallet.wallet_type and params.wallet.wallet_type != WalletType.CHIPI:
            raise ChipiSessionError(
                f"Session execution only supports CHIPI wallets. Got: {params.wallet.wallet_type}",
                SESSION_ERRORS["INVALID_WALLET_TYPE_FOR_SESSION"],
            )

        return execute_paymaster_transaction_with_session_sync(
            params={
                "encryptKey": params.encrypt_key,
                "wallet": {**params.wallet.model_dump(), "walletType": "CHIPI"},
                "session": params.session.model_dump(),
                "calls": [call.model_dump() for call in params.calls],
                "saveToDatabase": True,
            },
            bearer_token=bearer_token,
            client=self.client,
        )


def get_selector_from_name(name: str) -> int:
    """
    Get selector from function name.

    Args:
        name: Function name

    Returns:
        Selector as integer
    """
    from starknet_py.hash.selector import get_selector_from_name as _get_selector
    return _get_selector(name)
