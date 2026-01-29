"""Pollax API client"""

from typing import Optional
import time
import httpx

from .resources.agents import AgentsResource
from .resources.calls import CallsResource
from .resources.campaigns import CampaignsResource
from .resources.knowledge import KnowledgeResource
from .resources.analytics import AnalyticsResource
from .resources.integrations import IntegrationsResource
from .resources.phone_numbers import PhoneNumbersResource
from .resources.api_keys import ApiKeysResource
from .resources.voice_cloning import VoiceCloningResource
from .errors import PollaxError, AuthenticationError, NotFoundError, RateLimitError


class Pollax:
    """
    Pollax API client.
    
    Example:
        >>> from pollax import Pollax
        >>> client = Pollax(api_key="sk_live_...")
        >>> agent = client.agents.create(
        ...     name="Support Agent",
        ...     system_prompt="You are helpful",
        ... )
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.pollax.ai",
        timeout: float = 30.0,
        max_retries: int = 3,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize Pollax client.
        
        Args:
            api_key: Your Pollax API key (required)
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            tenant_id: Organization/tenant ID (optional)
        
        Raises:
            ValueError: If api_key is not provided
        """
        if not api_key:
            raise ValueError("API key is required. Get one at https://pollax.ai/settings/api-keys")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Pollax-SDK-Python/1.0.0",
        }

        if tenant_id:
            headers["X-Tenant-ID"] = tenant_id

        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )

        # Initialize resources
        self.agents = AgentsResource(self)
        self.calls = CallsResource(self)
        self.campaigns = CampaignsResource(self)
        self.knowledge = KnowledgeResource(self)
        self.analytics = AnalyticsResource(self)
        self.integrations = IntegrationsResource(self)
        self.phone_numbers = PhoneNumbersResource(self)
        self.api_keys = ApiKeysResource(self)
        self.voice_cloning = VoiceCloningResource(self)

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        files: Optional[dict] = None,
        _retries: int = 0,
    ) -> dict:
        """
        Make an HTTP request with automatic retries.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path
            json: JSON request body
            params: Query parameters
            files: Files to upload
            _retries: Internal retry counter
        
        Returns:
            Response data as dictionary
        
        Raises:
            PollaxError: On API errors
            AuthenticationError: On authentication failures
            NotFoundError: When resource not found
            RateLimitError: When rate limit exceeded
        """
        try:
            if files:
                # Remove Content-Type for multipart/form-data
                headers = {k: v for k, v in self.client.headers.items() if k != "Content-Type"}
                response = self.client.request(
                    method,
                    path,
                    params=params,
                    files=files,
                    headers=headers,
                )
            else:
                response = self.client.request(
                    method,
                    path,
                    json=json,
                    params=params,
                )

            response.raise_for_status()
            
            # Handle empty responses
            if not response.content:
                return {}
            
            return response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            
            # Handle rate limiting with exponential backoff
            if status_code == 429 and _retries < self.max_retries:
                retry_after = int(e.response.headers.get("Retry-After", "1"))
                time.sleep(retry_after)
                return self.request(method, path, json=json, params=params, files=files, _retries=_retries + 1)

            # Parse error message
            try:
                error_data = e.response.json()
                message = error_data.get("error") or error_data.get("detail", str(e))
            except Exception:
                message = str(e)

            # Raise appropriate error type
            if status_code == 401:
                raise AuthenticationError(message)
            elif status_code == 404:
                raise NotFoundError(message)
            elif status_code == 429:
                raise RateLimitError(message)
            else:
                raise PollaxError(message, status_code=status_code)

        except httpx.RequestError as e:
            # Retry on network errors
            if _retries < self.max_retries:
                delay = 2 ** _retries  # Exponential backoff
                time.sleep(delay)
                return self.request(method, path, json=json, params=params, files=files, _retries=_retries + 1)

            raise PollaxError(f"Network error: {str(e)}")

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "Pollax":
        """Context manager entry."""
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit."""
        self.close()
