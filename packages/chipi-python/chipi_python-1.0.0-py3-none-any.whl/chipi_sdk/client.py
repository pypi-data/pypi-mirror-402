"""HTTP client for Chipi API interactions."""

from typing import Any, Dict, Optional, TypeVar
import httpx

from .models.core import ChipiSDKConfig
from .errors import ChipiAuthError, ChipiApiError, handle_api_error
from .validators import is_valid_api_key, validate_error_response
from .constants import API_VERSION, API_VERSION_DATE, STARKNET_NETWORKS

T = TypeVar('T')


class ChipiClient:
    """HTTP client with sync and async support."""

    def __init__(self, config: ChipiSDKConfig):
        """
        Initialize the Chipi HTTP client.

        Args:
            config: SDK configuration

        Raises:
            ChipiAuthError: If API key is invalid
        """
        if not is_valid_api_key(config.api_public_key):
            raise ChipiAuthError("Invalid API key format")

        self.api_public_key = config.api_public_key
        self.custom_alpha_url = config.alpha_url
        self.base_url = self._get_base_url()
        self.node_url = config.node_url or STARKNET_NETWORKS["MAINNET"]
        self.sdk_version = "1.0.0"

        # Initialize HTTP clients
        self._sync_client = httpx.Client(timeout=30.0)
        self._async_client = httpx.AsyncClient(timeout=30.0)

    def get_api_public_key(self) -> str:
        """Get the API public key (for internal SDK use)."""
        return self.api_public_key

    def _get_base_url(self) -> str:
        """Construct the base API URL."""
        version = f"v{API_VERSION}"

        if self.custom_alpha_url:
            # Remove any existing version suffix and add the current one
            clean_url = self.custom_alpha_url.rstrip('/')
            # Remove existing version if present
            if clean_url.endswith(f'/v{API_VERSION}'):
                clean_url = clean_url[:-len(f'/v{API_VERSION}')]
            return f"{clean_url}/{version}"

        return f"https://celebrated-vision-production-66a5.up.railway.app/{version}"

    def _add_version_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add API version query parameters.

        Args:
            params: Existing parameters

        Returns:
            Parameters with version info added
        """
        if params is None:
            params = {}
        params["__chipi_api_version"] = API_VERSION_DATE
        return params

    def _get_headers(self, bearer_token: Optional[str] = None) -> Dict[str, str]:
        """
        Get HTTP headers for requests.

        Args:
            bearer_token: Optional bearer token for authentication

        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_public_key,
        }

        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        return headers

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        bearer_token: Optional[str] = None,
    ) -> Any:
        """
        Synchronous GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            bearer_token: Optional bearer token

        Returns:
            Response data

        Raises:
            ChipiApiError: If request fails
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Add version tracking parameters
            params = self._add_version_params(params or {})
            
            # Filter out None values
            params = {k: v for k, v in params.items() if v is not None}

            response = self._sync_client.get(
                url,
                params=params,
                headers=self._get_headers(bearer_token),
            )

            data = response.json()

            if not response.is_success:
                error_data = validate_error_response(data)
                raise ChipiApiError(
                    error_data["message"],
                    error_data.get("code", f"HTTP_{response.status_code}"),
                    response.status_code,
                )

            return data
        except ChipiApiError:
            raise
        except Exception as error:
            raise handle_api_error(error)

    async def aget(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        bearer_token: Optional[str] = None,
    ) -> Any:
        """
        Async GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            bearer_token: Optional bearer token

        Returns:
            Response data

        Raises:
            ChipiApiError: If request fails
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Add version tracking parameters
            params = self._add_version_params(params or {})
            
            # Filter out None values
            params = {k: v for k, v in params.items() if v is not None}

            response = await self._async_client.get(
                url,
                params=params,
                headers=self._get_headers(bearer_token),
            )

            data = response.json()

            if not response.is_success:
                error_data = validate_error_response(data)
                raise ChipiApiError(
                    error_data["message"],
                    error_data.get("code", f"HTTP_{response.status_code}"),
                    response.status_code,
                )

            return data
        except ChipiApiError:
            raise
        except Exception as error:
            raise handle_api_error(error)

    def post(
        self,
        endpoint: str,
        bearer_token: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Synchronous POST request.

        Args:
            endpoint: API endpoint path
            bearer_token: Bearer token for authentication
            body: Request body

        Returns:
            Response data

        Raises:
            ChipiApiError: If request fails
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Add version tracking to URL
            params = self._add_version_params({})

            response = self._sync_client.post(
                url,
                params=params,
                json=body,
                headers=self._get_headers(bearer_token),
            )

            data = response.json()

            if not response.is_success:
                error_data = validate_error_response(data)
                raise ChipiApiError(
                    error_data["message"],
                    error_data.get("code", f"HTTP_{response.status_code}"),
                    response.status_code,
                )

            return data
        except ChipiApiError:
            raise
        except Exception as error:
            raise handle_api_error(error)

    async def apost(
        self,
        endpoint: str,
        bearer_token: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Async POST request.

        Args:
            endpoint: API endpoint path
            bearer_token: Bearer token for authentication
            body: Request body

        Returns:
            Response data

        Raises:
            ChipiApiError: If request fails
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Add version tracking to URL
            params = self._add_version_params({})

            response = await self._async_client.post(
                url,
                params=params,
                json=body,
                headers=self._get_headers(bearer_token),
            )

            data = response.json()

            if not response.is_success:
                error_data = validate_error_response(data)
                raise ChipiApiError(
                    error_data["message"],
                    error_data.get("code", f"HTTP_{response.status_code}"),
                    response.status_code,
                )

            return data
        except ChipiApiError:
            raise
        except Exception as error:
            raise handle_api_error(error)

    def put(
        self,
        endpoint: str,
        bearer_token: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Synchronous PUT request.

        Args:
            endpoint: API endpoint path
            bearer_token: Bearer token for authentication
            body: Request body

        Returns:
            Response data

        Raises:
            ChipiApiError: If request fails
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Add version tracking to URL
            params = self._add_version_params({})

            response = self._sync_client.put(
                url,
                params=params,
                json=body,
                headers=self._get_headers(bearer_token),
            )

            data = response.json()

            if not response.is_success:
                error_data = validate_error_response(data)
                raise ChipiApiError(
                    error_data["message"],
                    error_data.get("code", f"HTTP_{response.status_code}"),
                    response.status_code,
                )

            return data
        except ChipiApiError:
            raise
        except Exception as error:
            raise handle_api_error(error)

    async def aput(
        self,
        endpoint: str,
        bearer_token: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Async PUT request.

        Args:
            endpoint: API endpoint path
            bearer_token: Bearer token for authentication
            body: Request body

        Returns:
            Response data

        Raises:
            ChipiApiError: If request fails
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Add version tracking to URL
            params = self._add_version_params({})

            response = await self._async_client.put(
                url,
                params=params,
                json=body,
                headers=self._get_headers(bearer_token),
            )

            data = response.json()

            if not response.is_success:
                error_data = validate_error_response(data)
                raise ChipiApiError(
                    error_data["message"],
                    error_data.get("code", f"HTTP_{response.status_code}"),
                    response.status_code,
                )

            return data
        except ChipiApiError:
            raise
        except Exception as error:
            raise handle_api_error(error)

    def delete(
        self,
        endpoint: str,
        bearer_token: str,
    ) -> Any:
        """
        Synchronous DELETE request.

        Args:
            endpoint: API endpoint path
            bearer_token: Bearer token for authentication

        Returns:
            Response data

        Raises:
            ChipiApiError: If request fails
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Add version tracking to URL
            params = self._add_version_params({})

            response = self._sync_client.delete(
                url,
                params=params,
                headers=self._get_headers(bearer_token),
            )

            data = response.json()

            if not response.is_success:
                error_data = validate_error_response(data)
                raise ChipiApiError(
                    error_data["message"],
                    error_data.get("code", f"HTTP_{response.status_code}"),
                    response.status_code,
                )

            return data
        except ChipiApiError:
            raise
        except Exception as error:
            raise handle_api_error(error)

    async def adelete(
        self,
        endpoint: str,
        bearer_token: str,
    ) -> Any:
        """
        Async DELETE request.

        Args:
            endpoint: API endpoint path
            bearer_token: Bearer token for authentication

        Returns:
            Response data

        Raises:
            ChipiApiError: If request fails
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Add version tracking to URL
            params = self._add_version_params({})

            response = await self._async_client.delete(
                url,
                params=params,
                headers=self._get_headers(bearer_token),
            )

            data = response.json()

            if not response.is_success:
                error_data = validate_error_response(data)
                raise ChipiApiError(
                    error_data["message"],
                    error_data.get("code", f"HTTP_{response.status_code}"),
                    response.status_code,
                )

            return data
        except ChipiApiError:
            raise
        except Exception as error:
            raise handle_api_error(error)

    def close(self):
        """Close the sync HTTP client."""
        self._sync_client.close()

    async def aclose(self):
        """Close the async HTTP client."""
        await self._async_client.aclose()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()
