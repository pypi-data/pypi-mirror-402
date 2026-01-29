"""API keys resource"""

from typing import List, Optional, TYPE_CHECKING
from ..models import ApiKey

if TYPE_CHECKING:
    from ..client import Pollax


class ApiKeysResource:
    """API Keys API resource"""

    def __init__(self, client: "Pollax"):
        self._client = client

    def create(self, name: str, permissions: Optional[List[str]] = None) -> dict:
        """Create a new API key."""
        return self._client.request(
            "POST",
            "/api/v1/api-keys",
            json={"name": name, "permissions": permissions or []},
        )

    def list(self) -> List[ApiKey]:
        """List all API keys."""
        response = self._client.request("GET", "/api/v1/api-keys")
        return [ApiKey(**item) for item in response]

    def revoke(self, key_id: str) -> dict:
        """Revoke an API key."""
        return self._client.request("DELETE", f"/api/v1/api-keys/{key_id}")
