"""User management."""

from .models.user import User, CreateUserParams, GetUserParams
from .constants import API_ENDPOINTS
from .client import ChipiClient


class ChipiUsers:
    """User management class."""

    def __init__(self, client: ChipiClient):
        """
        Initialize user manager.

        Args:
            client: Chipi HTTP client
        """
        self.client = client

    async def aget_user(self, params: GetUserParams, bearer_token: str) -> User:
        """
        Get user by external user ID (async).

        Args:
            params: User query parameters
            bearer_token: Authentication token

        Returns:
            User data
        """
        response = await self.client.aget(
            endpoint=f"{API_ENDPOINTS['USERS']}/by-external-id",
            params={"externalUserId": params.external_user_id},
            bearer_token=bearer_token,
        )
        return User(**response)

    def get_user(self, params: GetUserParams, bearer_token: str) -> User:
        """
        Get user by external user ID (sync).

        Args:
            params: User query parameters
            bearer_token: Authentication token

        Returns:
            User data
        """
        response = self.client.get(
            endpoint=f"{API_ENDPOINTS['USERS']}/by-external-id",
            params={"externalUserId": params.external_user_id},
            bearer_token=bearer_token,
        )
        return User(**response)

    async def acreate_user(
        self, params: CreateUserParams, bearer_token: str
    ) -> User:
        """
        Create a new user (async).

        Args:
            params: User creation parameters
            bearer_token: Authentication token

        Returns:
            Created user data
        """
        response = await self.client.apost(
            endpoint=API_ENDPOINTS["USERS"],
            bearer_token=bearer_token,
            body=params.model_dump(),
        )
        return User(**response)

    def create_user(self, params: CreateUserParams, bearer_token: str) -> User:
        """
        Create a new user (sync).

        Args:
            params: User creation parameters
            bearer_token: Authentication token

        Returns:
            Created user data
        """
        response = self.client.post(
            endpoint=API_ENDPOINTS["USERS"],
            bearer_token=bearer_token,
            body=params.model_dump(),
        )
        return User(**response)
