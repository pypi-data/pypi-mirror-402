"""SKU (Stock Keeping Unit) management."""

from .models.sku import Sku, GetSkuListQuery
from .models.core import PaginatedResponse
from .constants import API_ENDPOINTS
from .client import ChipiClient


class ChipiSkus:
    """SKU management class."""

    def __init__(self, client: ChipiClient):
        """
        Initialize SKU manager.

        Args:
            client: Chipi HTTP client
        """
        self.client = client

    async def aget_sku_list(
        self, params: GetSkuListQuery, bearer_token: str
    ) -> PaginatedResponse[Sku]:
        """
        Get paginated list of SKUs (async).

        Args:
            params: Query parameters for filtering SKUs
            bearer_token: Authentication token

        Returns:
            Paginated SKU list
        """
        response = await self.client.aget(
            endpoint=API_ENDPOINTS["SKUS"],
            params=params.model_dump(exclude_none=True),
            bearer_token=bearer_token,
        )
        return PaginatedResponse[Sku](**response)

    def get_sku_list(
        self, params: GetSkuListQuery, bearer_token: str
    ) -> PaginatedResponse[Sku]:
        """
        Get paginated list of SKUs (sync).

        Args:
            params: Query parameters for filtering SKUs
            bearer_token: Authentication token

        Returns:
            Paginated SKU list
        """
        response = self.client.get(
            endpoint=API_ENDPOINTS["SKUS"],
            params=params.model_dump(exclude_none=True),
            bearer_token=bearer_token,
        )
        return PaginatedResponse[Sku](**response)

    async def aget_sku(self, sku_id: str, bearer_token: str) -> Sku:
        """
        Get a specific SKU by ID (async).

        Args:
            sku_id: SKU identifier
            bearer_token: Authentication token

        Returns:
            SKU data
        """
        response = await self.client.aget(
            endpoint=f"{API_ENDPOINTS['SKUS']}/{sku_id}",
            bearer_token=bearer_token,
        )
        return Sku(**response)

    def get_sku(self, sku_id: str, bearer_token: str) -> Sku:
        """
        Get a specific SKU by ID (sync).

        Args:
            sku_id: SKU identifier
            bearer_token: Authentication token

        Returns:
            SKU data
        """
        response = self.client.get(
            endpoint=f"{API_ENDPOINTS['SKUS']}/{sku_id}",
            bearer_token=bearer_token,
        )
        return Sku(**response)
