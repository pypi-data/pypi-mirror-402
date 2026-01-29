"""Main Chipi SDK class for Starknet gasless transactions."""

from typing import Optional
from .models.core import ChipiSDKConfig, PaginatedResponse
from .models.wallet import (
    CreateWalletParams,
    CreateWalletResponse,
    GetWalletParams,
    GetWalletResponse,
    GetTokenBalanceParams,
    GetTokenBalanceResponse,
)
from .models.transaction import (
    ExecuteTransactionParams,
    TransferParams,
    ApproveParams,
    StakeVesuUsdcParams,
    WithdrawVesuUsdcParams,
    CallAnyContractParams,
    RecordSendTransactionParams,
    Transaction,
    GetTransactionListQuery,
    Call,
)
from .models.session import ExecuteWithSessionParams
from .models.sku import Sku, GetSkuListQuery
from .models.sku_transaction import CreateSkuTransactionParams, SkuTransaction
from .models.user import User, CreateUserParams, GetUserParams
from .client import ChipiClient
from .wallets import ChipiWallets
from .transactions import ChipiTransactions
from .sessions import ChipiSessions
from .skus import ChipiSkus
from .sku_transactions import ChipiSkuTransactions
from .users import ChipiUsers
from .formatters import format_amount
from .constants import STARKNET_NETWORKS, CONTRACT_ADDRESSES


class ChipiSDK:
    """Main Chipi SDK class for Starknet gasless transactions."""

    def __init__(self, config: ChipiSDKConfig):
        """
        Initialize the Chipi SDK.

        Args:
            config: SDK configuration with API keys and optional URLs
        """
        self.client = ChipiClient(config)
        self.node_url = config.node_url or STARKNET_NETWORKS["MAINNET"]
        self.api_secret_key = config.api_secret_key

        # Initialize service managers
        self.wallets = ChipiWallets(self.client)
        self.transactions = ChipiTransactions(self.client)
        self.sessions = ChipiSessions(self.client)
        self.skus = ChipiSkus(self.client)
        self.sku_transactions = ChipiSkuTransactions(self.client)
        self.users = ChipiUsers(self.client)

    def _resolve_bearer_token(self, bearer_token: Optional[str] = None) -> str:
        """
        Resolve bearer token - uses provided token or falls back to apiSecretKey.

        Args:
            bearer_token: Optional bearer token

        Returns:
            Resolved bearer token

        Raises:
            ValueError: If no token is available
        """
        token = bearer_token or self.api_secret_key

        if not token:
            raise ValueError(
                "Authentication required: either pass a bearerToken or configure the SDK with an apiSecretKey"
            )

        return token

    # ===== Transaction Methods =====

    async def aexecute_transaction(
        self,
        params: ExecuteTransactionParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Execute a gasless transaction (async).

        Args:
            params: Transaction execution parameters
            bearer_token: Optional bearer token (falls back to SDK config)

        Returns:
            Transaction hash
        """
        return await self.transactions.aexecute_transaction(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def execute_transaction(
        self,
        params: ExecuteTransactionParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Execute a gasless transaction (sync).

        Args:
            params: Transaction execution parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        return self.transactions.execute_transaction(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    async def aexecute_transaction_with_session(
        self,
        params: ExecuteWithSessionParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Execute a gasless transaction using a session key (async).

        CHIPI wallets only.

        Args:
            params: Session execution parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        return await self.sessions.aexecute_transaction_with_session(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def execute_transaction_with_session(
        self,
        params: ExecuteWithSessionParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Execute a gasless transaction using a session key (sync).

        Args:
            params: Session execution parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        return self.sessions.execute_transaction_with_session(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    async def atransfer(
        self,
        params: TransferParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Transfer tokens (async).

        Args:
            params: Transfer parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        return await self.transactions.atransfer(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def transfer(
        self,
        params: TransferParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Transfer tokens (sync).

        Args:
            params: Transfer parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        return self.transactions.transfer(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    async def aapprove(
        self,
        params: ApproveParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Approve token spending (async).

        Args:
            params: Approval parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        return await self.transactions.aapprove(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def approve(
        self,
        params: ApproveParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Approve token spending (sync).

        Args:
            params: Approval parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        return self.transactions.approve(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    async def astake_vesu_usdc(
        self,
        params: StakeVesuUsdcParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Stake USDC in Vesu protocol (async).

        Args:
            params: Staking parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        formatted_amount = format_amount(params.amount, 6)

        return await self.aexecute_transaction(
            params=ExecuteTransactionParams(
                encrypt_key=params.encrypt_key,
                wallet=params.wallet,
                calls=[
                    Call(
                        contractAddress=CONTRACT_ADDRESSES["USDC_MAINNET"],
                        entrypoint="approve",
                        calldata=[
                            CONTRACT_ADDRESSES["VESU_USDC_MAINNET"],
                            formatted_amount,
                            "0x0",
                        ],
                    ),
                    Call(
                        contractAddress=CONTRACT_ADDRESSES["VESU_USDC_MAINNET"],
                        entrypoint="deposit",
                        calldata=[formatted_amount, "0x0", params.receiver_wallet],
                    ),
                ],
            ),
            bearer_token=bearer_token,
        )

    def stake_vesu_usdc(
        self,
        params: StakeVesuUsdcParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Stake USDC in Vesu protocol (sync).

        Args:
            params: Staking parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        formatted_amount = format_amount(params.amount, 6)

        return self.execute_transaction(
            params=ExecuteTransactionParams(
                encrypt_key=params.encrypt_key,
                wallet=params.wallet,
                calls=[
                    Call(
                        contractAddress=CONTRACT_ADDRESSES["USDC_MAINNET"],
                        entrypoint="approve",
                        calldata=[
                            CONTRACT_ADDRESSES["VESU_USDC_MAINNET"],
                            formatted_amount,
                            "0x0",
                        ],
                    ),
                    Call(
                        contractAddress=CONTRACT_ADDRESSES["VESU_USDC_MAINNET"],
                        entrypoint="deposit",
                        calldata=[formatted_amount, "0x0", params.receiver_wallet],
                    ),
                ],
            ),
            bearer_token=bearer_token,
        )

    async def awithdraw_vesu_usdc(
        self,
        params: WithdrawVesuUsdcParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Withdraw USDC from Vesu protocol (async).

        Args:
            params: Withdrawal parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        formatted_amount = format_amount(params.amount, 6)

        return await self.aexecute_transaction(
            params=ExecuteTransactionParams(
                encrypt_key=params.encrypt_key,
                wallet=params.wallet,
                calls=[
                    Call(
                        contractAddress=CONTRACT_ADDRESSES["VESU_USDC_MAINNET"],
                        entrypoint="withdraw",
                        calldata=[formatted_amount, params.recipient, "0x0"],
                    )
                ],
            ),
            bearer_token=bearer_token,
        )

    def withdraw_vesu_usdc(
        self,
        params: WithdrawVesuUsdcParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Withdraw USDC from Vesu protocol (sync).

        Args:
            params: Withdrawal parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        formatted_amount = format_amount(params.amount, 6)

        return self.execute_transaction(
            params=ExecuteTransactionParams(
                encrypt_key=params.encrypt_key,
                wallet=params.wallet,
                calls=[
                    Call(
                        contractAddress=CONTRACT_ADDRESSES["VESU_USDC_MAINNET"],
                        entrypoint="withdraw",
                        calldata=[formatted_amount, params.recipient, "0x0"],
                    )
                ],
            ),
            bearer_token=bearer_token,
        )

    async def acall_any_contract(
        self,
        params: CallAnyContractParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Call any contract method (async).

        Args:
            params: Contract call parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        return await self.aexecute_transaction(
            params=ExecuteTransactionParams(
                encrypt_key=params.encrypt_key,
                wallet=params.wallet,
                calls=params.calls,
                use_passkey=params.use_passkey,
            ),
            bearer_token=bearer_token,
        )

    def call_any_contract(
        self,
        params: CallAnyContractParams,
        bearer_token: Optional[str] = None,
    ) -> str:
        """
        Call any contract method (sync).

        Args:
            params: Contract call parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction hash
        """
        return self.execute_transaction(
            params=ExecuteTransactionParams(
                encrypt_key=params.encrypt_key,
                wallet=params.wallet,
                calls=params.calls,
                use_passkey=params.use_passkey,
            ),
            bearer_token=bearer_token,
        )

    # ===== Wallet Methods =====

    async def acreate_wallet(
        self,
        params: CreateWalletParams,
        bearer_token: Optional[str] = None,
    ) -> CreateWalletResponse:
        """
        Create a new wallet (async).

        Args:
            params: Wallet creation parameters
            bearer_token: Optional bearer token

        Returns:
            Wallet creation response
        """
        return await self.wallets.acreate_wallet(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def create_wallet(
        self,
        params: CreateWalletParams,
        bearer_token: Optional[str] = None,
    ) -> CreateWalletResponse:
        """
        Create a new wallet (sync).

        Args:
            params: Wallet creation parameters
            bearer_token: Optional bearer token

        Returns:
            Wallet creation response
        """
        return self.wallets.create_wallet(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    async def aget_wallet(
        self,
        params: GetWalletParams,
        bearer_token: Optional[str] = None,
    ) -> Optional[GetWalletResponse]:
        """
        Get wallet by external user ID (async).

        Args:
            params: Wallet query parameters
            bearer_token: Optional bearer token

        Returns:
            Wallet data or None if not found
        """
        return await self.wallets.aget_wallet(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def get_wallet(
        self,
        params: GetWalletParams,
        bearer_token: Optional[str] = None,
    ) -> Optional[GetWalletResponse]:
        """
        Get wallet by external user ID (sync).

        Args:
            params: Wallet query parameters
            bearer_token: Optional bearer token

        Returns:
            Wallet data or None if not found
        """
        return self.wallets.get_wallet(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    async def aget_token_balance(
        self,
        params: GetTokenBalanceParams,
        bearer_token: Optional[str] = None,
    ) -> GetTokenBalanceResponse:
        """
        Get token balance (async).

        Args:
            params: Balance query parameters
            bearer_token: Optional bearer token

        Returns:
            Token balance
        """
        return await self.wallets.aget_token_balance(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def get_token_balance(
        self,
        params: GetTokenBalanceParams,
        bearer_token: Optional[str] = None,
    ) -> GetTokenBalanceResponse:
        """
        Get token balance (sync).

        Args:
            params: Balance query parameters
            bearer_token: Optional bearer token

        Returns:
            Token balance
        """
        return self.wallets.get_token_balance(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    # ===== Transaction History =====

    async def arecord_send_transaction(
        self,
        params: RecordSendTransactionParams,
        bearer_token: Optional[str] = None,
    ) -> Transaction:
        """
        Record a send transaction (async).

        Args:
            params: Transaction recording parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction record
        """
        return await self.transactions.arecord_send_transaction(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def record_send_transaction(
        self,
        params: RecordSendTransactionParams,
        bearer_token: Optional[str] = None,
    ) -> Transaction:
        """
        Record a send transaction (sync).

        Args:
            params: Transaction recording parameters
            bearer_token: Optional bearer token

        Returns:
            Transaction record
        """
        return self.transactions.record_send_transaction(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    async def aget_transaction_list(
        self,
        query: GetTransactionListQuery,
        bearer_token: Optional[str] = None,
    ) -> PaginatedResponse[Transaction]:
        """
        Get transaction list (async).

        Args:
            query: Query parameters
            bearer_token: Optional bearer token

        Returns:
            Paginated transaction list
        """
        return await self.transactions.aget_transaction_list(
            query=query,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def get_transaction_list(
        self,
        query: GetTransactionListQuery,
        bearer_token: Optional[str] = None,
    ) -> PaginatedResponse[Transaction]:
        """
        Get transaction list (sync).

        Args:
            query: Query parameters
            bearer_token: Optional bearer token

        Returns:
            Paginated transaction list
        """
        return self.transactions.get_transaction_list(
            query=query,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    # ===== SKU Methods =====

    async def aget_sku_list(
        self,
        params: GetSkuListQuery,
        bearer_token: Optional[str] = None,
    ) -> PaginatedResponse[Sku]:
        """
        Get SKU list (async).

        Args:
            params: Query parameters
            bearer_token: Optional bearer token

        Returns:
            Paginated SKU list
        """
        return await self.skus.aget_sku_list(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def get_sku_list(
        self,
        params: GetSkuListQuery,
        bearer_token: Optional[str] = None,
    ) -> PaginatedResponse[Sku]:
        """
        Get SKU list (sync).

        Args:
            params: Query parameters
            bearer_token: Optional bearer token

        Returns:
            Paginated SKU list
        """
        return self.skus.get_sku_list(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    async def aget_sku(
        self,
        sku_id: str,
        bearer_token: Optional[str] = None,
    ) -> Sku:
        """
        Get SKU by ID (async).

        Args:
            sku_id: SKU identifier
            bearer_token: Optional bearer token

        Returns:
            SKU data
        """
        return await self.skus.aget_sku(
            sku_id=sku_id,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def get_sku(
        self,
        sku_id: str,
        bearer_token: Optional[str] = None,
    ) -> Sku:
        """
        Get SKU by ID (sync).

        Args:
            sku_id: SKU identifier
            bearer_token: Optional bearer token

        Returns:
            SKU data
        """
        return self.skus.get_sku(
            sku_id=sku_id,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    async def acreate_sku_transaction(
        self,
        params: CreateSkuTransactionParams,
        bearer_token: Optional[str] = None,
    ) -> SkuTransaction:
        """
        Create SKU transaction (async).

        Args:
            params: SKU transaction parameters
            bearer_token: Optional bearer token

        Returns:
            SKU transaction
        """
        return await self.sku_transactions.acreate_sku_transaction(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def create_sku_transaction(
        self,
        params: CreateSkuTransactionParams,
        bearer_token: Optional[str] = None,
    ) -> SkuTransaction:
        """
        Create SKU transaction (sync).

        Args:
            params: SKU transaction parameters
            bearer_token: Optional bearer token

        Returns:
            SKU transaction
        """
        return self.sku_transactions.create_sku_transaction(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    # ===== User Methods =====

    async def aget_user(
        self,
        params: GetUserParams,
        bearer_token: Optional[str] = None,
    ) -> User:
        """
        Get user by external ID (async).

        Args:
            params: User query parameters
            bearer_token: Optional bearer token

        Returns:
            User data
        """
        return await self.users.aget_user(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def get_user(
        self,
        params: GetUserParams,
        bearer_token: Optional[str] = None,
    ) -> User:
        """
        Get user by external ID (sync).

        Args:
            params: User query parameters
            bearer_token: Optional bearer token

        Returns:
            User data
        """
        return self.users.get_user(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    async def acreate_user(
        self,
        params: CreateUserParams,
        bearer_token: Optional[str] = None,
    ) -> User:
        """
        Create user (async).

        Args:
            params: User creation parameters
            bearer_token: Optional bearer token

        Returns:
            Created user
        """
        return await self.users.acreate_user(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )

    def create_user(
        self,
        params: CreateUserParams,
        bearer_token: Optional[str] = None,
    ) -> User:
        """
        Create user (sync).

        Args:
            params: User creation parameters
            bearer_token: Optional bearer token

        Returns:
            Created user
        """
        return self.users.create_user(
            params=params,
            bearer_token=self._resolve_bearer_token(bearer_token),
        )
