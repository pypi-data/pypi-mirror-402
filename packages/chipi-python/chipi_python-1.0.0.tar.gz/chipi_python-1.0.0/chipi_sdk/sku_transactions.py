"""SKU transaction management."""

from .models.sku_transaction import CreateSkuTransactionParams, SkuTransaction
from .constants import API_ENDPOINTS
from .client import ChipiClient


class ChipiSkuTransactions:
    """SKU transaction management class."""

    def __init__(self, client: ChipiClient):
        """
        Initialize SKU transaction manager.

        Args:
            client: Chipi HTTP client
        """
        self.client = client

    async def acreate_sku_transaction(
        self, params: CreateSkuTransactionParams, bearer_token: str
    ) -> SkuTransaction:
        """
        Create a new SKU transaction (async).

        Args:
            params: SKU transaction creation parameters
            bearer_token: Authentication token

        Returns:
            Created SKU transaction
        """
        response = await self.client.apost(
            endpoint=API_ENDPOINTS["SKU_TRANSACTIONS"],
            bearer_token=bearer_token,
            body=params.model_dump(),
        )
        return SkuTransaction(**response)

    def create_sku_transaction(
        self, params: CreateSkuTransactionParams, bearer_token: str
    ) -> SkuTransaction:
        """
        Create a new SKU transaction (sync).

        Args:
            params: SKU transaction creation parameters
            bearer_token: Authentication token

        Returns:
            Created SKU transaction
        """
        response = self.client.post(
            endpoint=API_ENDPOINTS["SKU_TRANSACTIONS"],
            bearer_token=bearer_token,
            body=params.model_dump(),
        )
        return SkuTransaction(**response)
