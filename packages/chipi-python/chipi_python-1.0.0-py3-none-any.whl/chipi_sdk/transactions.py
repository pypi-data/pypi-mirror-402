"""Transaction management utilities."""

from typing import Optional
from .models.transaction import (
    ExecuteTransactionParams,
    TransferParams,
    ApproveParams,
    CallAnyContractParams,
    RecordSendTransactionParams,
    Transaction,
    GetTransactionListQuery,
)
from .models.core import PaginatedResponse, STARKNET_CONTRACTS
from .models.wallet import WalletData
from .formatters import format_amount
from .constants import API_ENDPOINTS
from .client import ChipiClient
from .execute_paymaster import (
    execute_paymaster_transaction,
    execute_paymaster_transaction_sync,
)


class ChipiTransactions:
    """Transaction management class."""

    def __init__(self, client: ChipiClient):
        """
        Initialize transaction manager.

        Args:
            client: Chipi HTTP client
        """
        self.client = client

    async def aexecute_transaction(
        self,
        params: ExecuteTransactionParams,
        bearer_token: str,
        save_to_database: bool = True,
    ) -> str:
        """
        Execute a gasless transaction using paymaster (async).

        Args:
            params: Transaction execution parameters
            bearer_token: Authentication token
            save_to_database: Whether to save transaction to database (internal)

        Returns:
            Transaction hash
        """
        return await execute_paymaster_transaction(
            params={
                "encryptKey": params.encrypt_key,
                "wallet": params.wallet.model_dump(),
                "calls": [call.model_dump(by_alias=True) for call in params.calls],
                "saveToDatabase": save_to_database,
                "usePasskey": params.use_passkey,
            },
            bearer_token=bearer_token,
            client=self.client,
        )

    def execute_transaction(
        self,
        params: ExecuteTransactionParams,
        bearer_token: str,
        save_to_database: bool = True,
    ) -> str:
        """
        Execute a gasless transaction using paymaster (sync).

        Args:
            params: Transaction execution parameters
            bearer_token: Authentication token
            save_to_database: Whether to save transaction to database (internal)

        Returns:
            Transaction hash
        """
        return execute_paymaster_transaction_sync(
            params={
                "encryptKey": params.encrypt_key,
                "wallet": params.wallet.model_dump(),
                "calls": [call.model_dump(by_alias=True) for call in params.calls],
                "saveToDatabase": save_to_database,
                "usePasskey": params.use_passkey,
            },
            bearer_token=bearer_token,
            client=self.client,
        )

    async def atransfer(
        self, params: TransferParams, bearer_token: str
    ) -> str:
        """
        Transfer tokens (async).

        Args:
            params: Transfer parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash
        """
        contract = STARKNET_CONTRACTS[params.token]
        contract_address = contract.contract_address
        decimals = contract.decimals

        if params.token.value == "OTHER":
            if not params.other_token:
                raise ValueError("other_token is required when token is OTHER")
            contract_address = params.other_token["contractAddress"]
            decimals = params.other_token["decimals"]

        formatted_amount = format_amount(params.amount, decimals)

        from .models.transaction import Call, ExecuteTransactionParams

        return await self.aexecute_transaction(
            params=ExecuteTransactionParams(
                encrypt_key=params.encrypt_key,
                wallet=params.wallet,
                calls=[
                    Call(
                        contractAddress=contract_address,
                        entrypoint="transfer",
                        calldata=[params.recipient, formatted_amount, "0x0"],
                    )
                ],
                use_passkey=params.use_passkey,
            ),
            bearer_token=bearer_token,
        )

    def transfer(self, params: TransferParams, bearer_token: str) -> str:
        """
        Transfer tokens (sync).

        Args:
            params: Transfer parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash
        """
        contract = STARKNET_CONTRACTS[params.token]
        contract_address = contract.contract_address
        decimals = contract.decimals

        if params.token.value == "OTHER":
            if not params.other_token:
                raise ValueError("other_token is required when token is OTHER")
            contract_address = params.other_token["contractAddress"]
            decimals = params.other_token["decimals"]

        formatted_amount = format_amount(params.amount, decimals)

        from .models.transaction import Call, ExecuteTransactionParams

        return self.execute_transaction(
            params=ExecuteTransactionParams(
                encrypt_key=params.encrypt_key,
                wallet=params.wallet,
                calls=[
                    Call(
                        contractAddress=contract_address,
                        entrypoint="transfer",
                        calldata=[params.recipient, formatted_amount, "0x0"],
                    )
                ],
                use_passkey=params.use_passkey,
            ),
            bearer_token=bearer_token,
        )

    async def aapprove(
        self, params: ApproveParams, bearer_token: str
    ) -> str:
        """
        Approve token spending (async).

        Args:
            params: Approval parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash
        """
        formatted_amount = format_amount(params.amount, params.decimals or 18)

        from .models.transaction import Call, ExecuteTransactionParams

        return await self.aexecute_transaction(
            params=ExecuteTransactionParams(
                encrypt_key=params.encrypt_key,
                wallet=params.wallet,
                calls=[
                    Call(
                        contractAddress=params.contract_address,
                        entrypoint="approve",
                        calldata=[params.spender, formatted_amount, "0x0"],
                    )
                ],
                use_passkey=params.use_passkey,
            ),
            bearer_token=bearer_token,
        )

    def approve(self, params: ApproveParams, bearer_token: str) -> str:
        """
        Approve token spending (sync).

        Args:
            params: Approval parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash
        """
        formatted_amount = format_amount(params.amount, params.decimals or 18)

        from .models.transaction import Call, ExecuteTransactionParams

        return self.execute_transaction(
            params=ExecuteTransactionParams(
                encrypt_key=params.encrypt_key,
                wallet=params.wallet,
                calls=[
                    Call(
                        contractAddress=params.contract_address,
                        entrypoint="approve",
                        calldata=[params.spender, formatted_amount, "0x0"],
                    )
                ],
                use_passkey=params.use_passkey,
            ),
            bearer_token=bearer_token,
        )

    async def acall_any_contract(
        self, params: CallAnyContractParams, bearer_token: str
    ) -> str:
        """
        Call any contract method (async).

        Args:
            params: Contract call parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash
        """
        from .models.transaction import ExecuteTransactionParams

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
        self, params: CallAnyContractParams, bearer_token: str
    ) -> str:
        """
        Call any contract method (sync).

        Args:
            params: Contract call parameters
            bearer_token: Authentication token

        Returns:
            Transaction hash
        """
        from .models.transaction import ExecuteTransactionParams

        return self.execute_transaction(
            params=ExecuteTransactionParams(
                encrypt_key=params.encrypt_key,
                wallet=params.wallet,
                calls=params.calls,
                use_passkey=params.use_passkey,
            ),
            bearer_token=bearer_token,
        )

    async def arecord_send_transaction(
        self, params: RecordSendTransactionParams, bearer_token: str
    ) -> Transaction:
        """
        Record a send transaction (async).

        Args:
            params: Transaction recording parameters
            bearer_token: Authentication token

        Returns:
            Transaction record
        """
        response = await self.client.apost(
            endpoint=f"{API_ENDPOINTS['TRANSACTIONS']}/record-send",
            bearer_token=bearer_token,
            body=params.model_dump(),
        )
        return Transaction(**response)

    def record_send_transaction(
        self, params: RecordSendTransactionParams, bearer_token: str
    ) -> Transaction:
        """
        Record a send transaction (sync).

        Args:
            params: Transaction recording parameters
            bearer_token: Authentication token

        Returns:
            Transaction record
        """
        response = self.client.post(
            endpoint=f"{API_ENDPOINTS['TRANSACTIONS']}/record-send",
            bearer_token=bearer_token,
            body=params.model_dump(),
        )
        return Transaction(**response)

    async def aget_transaction_list(
        self, query: GetTransactionListQuery, bearer_token: str
    ) -> PaginatedResponse[Transaction]:
        """
        Get paginated transaction history (async).

        Args:
            query: Query parameters for filtering transactions
            bearer_token: Authentication token

        Returns:
            Paginated transaction list
        """
        response = await self.client.aget(
            endpoint=f"{API_ENDPOINTS['TRANSACTIONS']}/transaction-list",
            params=query.model_dump(exclude_none=True),
            bearer_token=bearer_token,
        )
        return PaginatedResponse[Transaction](**response)

    def get_transaction_list(
        self, query: GetTransactionListQuery, bearer_token: str
    ) -> PaginatedResponse[Transaction]:
        """
        Get paginated transaction history (sync).

        Args:
            query: Query parameters for filtering transactions
            bearer_token: Authentication token

        Returns:
            Paginated transaction list
        """
        response = self.client.get(
            endpoint=f"{API_ENDPOINTS['TRANSACTIONS']}/transaction-list",
            params=query.model_dump(exclude_none=True),
            bearer_token=bearer_token,
        )
        return PaginatedResponse[Transaction](**response)
