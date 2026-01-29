"""Wallet management utilities."""

import os
import secrets
from typing import Optional
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.account.account import Account
from starknet_py.net.models import StarknetChainId
from starknet_py.hash.address import compute_address
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.cairo.felt import encode_shortstring

from .models.wallet import (
    CreateWalletParams,
    CreateWalletResponse,
    GetWalletParams,
    GetWalletResponse,
    GetTokenBalanceParams,
    GetTokenBalanceResponse,
    WalletType,
    WalletData,
    DeploymentData,
    CreateCustodialWalletParams,
)
from .encryption import encrypt_private_key
from .errors import ChipiTransactionError, ChipiApiError
from .constants import (
    API_ENDPOINTS,
    WALLET_CLASS_HASHES,
    WALLET_RPC_ENDPOINTS,
)
from .client import ChipiClient


class ChipiWallets:
    """Wallet management class."""

    def __init__(self, client: ChipiClient):
        """
        Initialize wallet manager.

        Args:
            client: Chipi HTTP client
        """
        self.client = client

    def _get_private_key(self) -> str:
        """
        Generate a random private key compatible with Starknet.

        Returns:
            Private key as hex string with 0x prefix
        """
        # Generate 32 random bytes (256 bits)
        private_key_bytes = secrets.token_bytes(32)
        private_key = private_key_bytes.hex()
        full_private_key = f"0x{private_key}"

        # Ensure the private key is within Starknet's valid range (0 to 2^251 - 1)
        max_starknet_value = 2**251
        private_key_int = int(full_private_key, 16) % max_starknet_value

        # Convert back to hex string with '0x' prefix
        return f"0x{private_key_int:064x}"

    def _build_constructor_calldata(
        self, wallet_type: WalletType, stark_key_pub: str
    ) -> list[int]:
        """
        Build constructor calldata based on wallet type.

        Args:
            wallet_type: Type of wallet (CHIPI or READY)
            stark_key_pub: Public key

        Returns:
            List of calldata values as integers
        """
        if wallet_type == WalletType.READY:
            # Argent X Account: owner (CairoCustomEnum) + guardian (CairoOption None)
            # This is a simplified version - full Cairo enum encoding needed
            # For now, return basic structure
            return [int(stark_key_pub, 16), 0]  # owner pubkey, no guardian

        # CHIPI wallet: Simple OpenZeppelin account with just public_key
        return [int(stark_key_pub, 16)]

    async def acreate_wallet(
        self, params: CreateWalletParams, bearer_token: str
    ) -> CreateWalletResponse:
        """
        Create a new wallet (async).

        Args:
            params: Wallet creation parameters
            bearer_token: Authentication token

        Returns:
            Wallet creation response with transaction hash and wallet data

        Raises:
            ChipiTransactionError: If wallet creation fails
        """
        try:
            encrypt_key = params.encrypt_key
            external_user_id = params.external_user_id
            user_id = params.user_id
            wallet_type = params.wallet_type or WalletType.CHIPI
            use_passkey = params.use_passkey or False

            if not encrypt_key:
                error_msg = (
                    "encryptKey is required when using passkey. The passkey authentication should have provided the encryptKey."
                    if use_passkey
                    else "encryptKey is required for wallet creation"
                )
                raise ValueError(error_msg)

            # Select RPC endpoint based on wallet type
            rpc_url = WALLET_RPC_ENDPOINTS.get(
                wallet_type, WALLET_RPC_ENDPOINTS[WalletType.CHIPI]
            )

            provider = FullNodeClient(node_url=rpc_url)

            # Generate private key
            private_key_ax = self._get_private_key()
            
            # Get public key from private key
            from starknet_py.net.signer.stark_curve_signer import KeyPair
            key_pair = KeyPair.from_private_key(int(private_key_ax, 16))
            stark_key_pub_ax = hex(key_pair.public_key)

            # Select class hash based on wallet type
            account_class_hash = WALLET_CLASS_HASHES.get(
                wallet_type, WALLET_CLASS_HASHES[WalletType.CHIPI]
            )

            # Build constructor calldata
            constructor_calldata = self._build_constructor_calldata(
                wallet_type, stark_key_pub_ax
            )

            # Calculate future address of the account
            public_key = compute_address(
                salt=int(stark_key_pub_ax, 16),
                class_hash=int(account_class_hash, 16),
                constructor_calldata=constructor_calldata,
                deployer_address=0,
            )
            public_key_hex = hex(public_key)

            # Create account instance
            account = Account(
                client=provider,
                address=public_key_hex,
                key_pair=key_pair,
                chain=StarknetChainId.MAINNET,
            )

            # Prepare wallet creation via API
            typed_data_response = await self.client.apost(
                endpoint=f"{API_ENDPOINTS['CHIPI_WALLETS']}/prepare-creation",
                bearer_token=bearer_token,
                body={
                    "publicKey": public_key_hex,
                    "walletType": wallet_type.value,
                    "starkKeyPubAX": stark_key_pub_ax,
                },
            )

            typed_data = typed_data_response["typedData"]
            account_class_hash_response = typed_data_response["accountClassHash"]

            # Sign the typed data
            user_signature = account.sign_message(typed_data)

            # Prepare deployment data
            deployment_data = {
                "class_hash": account_class_hash_response,
                "salt": stark_key_pub_ax,
                "unique": hex(0),
                "calldata": [hex(val) for val in constructor_calldata],
            }

            # Encrypt private key
            encrypted_private_key = encrypt_private_key(private_key_ax, encrypt_key)

            # Create wallet via API
            response = await self.client.apost(
                endpoint=API_ENDPOINTS["CHIPI_WALLETS"],
                bearer_token=bearer_token,
                body={
                    "externalUserId": external_user_id,
                    "userId": user_id,
                    "publicKey": public_key_hex,
                    "walletType": wallet_type.value,
                    "userSignature": {
                        "r": str(user_signature[0]),
                        "s": str(user_signature[1]),
                        "recovery": 0,
                    },
                    "typedData": typed_data,
                    "encryptedPrivateKey": encrypted_private_key,
                    "deploymentData": deployment_data,
                },
            )

            return CreateWalletResponse(**response)
        except Exception as error:
            print(f"Detailed error: {error}")
            raise ChipiTransactionError(
                f"Failed to create wallet: {str(error)}", "WALLET_CREATION_FAILED"
            )

    def create_wallet(
        self, params: CreateWalletParams, bearer_token: str
    ) -> CreateWalletResponse:
        """
        Create a new wallet (sync).

        Args:
            params: Wallet creation parameters
            bearer_token: Authentication token

        Returns:
            Wallet creation response

        Raises:
            ChipiTransactionError: If wallet creation fails
        """
        # Sync version - simplified, users should prefer async
        import asyncio
        return asyncio.run(self.acreate_wallet(params, bearer_token))

    async def aget_wallet(
        self, params: GetWalletParams, bearer_token: str
    ) -> Optional[GetWalletResponse]:
        """
        Retrieve a wallet by external user ID (async).

        Args:
            params: Wallet query parameters
            bearer_token: Authentication token

        Returns:
            Wallet data or None if not found

        Raises:
            ChipiApiError: If request fails (except 404)
        """
        try:
            response = await self.client.aget(
                endpoint=f"{API_ENDPOINTS['CHIPI_WALLETS']}/by-user",
                params={"externalUserId": params.external_user_id},
                bearer_token=bearer_token,
            )
            return GetWalletResponse(**response)
        except ChipiApiError as err:
            if err.status == 404:
                return None
            raise

    def get_wallet(
        self, params: GetWalletParams, bearer_token: str
    ) -> Optional[GetWalletResponse]:
        """
        Retrieve a wallet by external user ID (sync).

        Args:
            params: Wallet query parameters
            bearer_token: Authentication token

        Returns:
            Wallet data or None if not found
        """
        try:
            response = self.client.get(
                endpoint=f"{API_ENDPOINTS['CHIPI_WALLETS']}/by-user",
                params={"externalUserId": params.external_user_id},
                bearer_token=bearer_token,
            )
            return GetWalletResponse(**response)
        except ChipiApiError as err:
            if err.status == 404:
                return None
            raise

    async def aget_token_balance(
        self, params: GetTokenBalanceParams, bearer_token: str
    ) -> GetTokenBalanceResponse:
        """
        Query token balance (async).

        Args:
            params: Balance query parameters
            bearer_token: Authentication token

        Returns:
            Token balance information
        """
        response = await self.client.aget(
            endpoint=f"{API_ENDPOINTS['CHIPI_WALLETS']}/token-balance",
            params=params.model_dump(exclude_none=True),
            bearer_token=bearer_token,
        )
        return GetTokenBalanceResponse(**response)

    def get_token_balance(
        self, params: GetTokenBalanceParams, bearer_token: str
    ) -> GetTokenBalanceResponse:
        """
        Query token balance (sync).

        Args:
            params: Balance query parameters
            bearer_token: Authentication token

        Returns:
            Token balance information
        """
        response = self.client.get(
            endpoint=f"{API_ENDPOINTS['CHIPI_WALLETS']}/token-balance",
            params=params.model_dump(exclude_none=True),
            bearer_token=bearer_token,
        )
        return GetTokenBalanceResponse(**response)

    async def acreate_custodial_wallet(
        self, params: CreateCustodialWalletParams, bearer_token: str
    ) -> WalletData:
        """
        Create a custodial merchant wallet (async).

        Args:
            params: Custodial wallet parameters
            bearer_token: Authentication token

        Returns:
            Wallet data
        """
        response = await self.client.apost(
            endpoint=f"{API_ENDPOINTS['CHIPI_WALLETS']}/custodial",
            bearer_token=bearer_token,
            body=params.model_dump(),
        )
        return WalletData(**response)

    def create_custodial_wallet(
        self, params: CreateCustodialWalletParams, bearer_token: str
    ) -> WalletData:
        """
        Create a custodial merchant wallet (sync).

        Args:
            params: Custodial wallet parameters
            bearer_token: Authentication token

        Returns:
            Wallet data
        """
        response = self.client.post(
            endpoint=f"{API_ENDPOINTS['CHIPI_WALLETS']}/custodial",
            bearer_token=bearer_token,
            body=params.model_dump(),
        )
        return WalletData(**response)
