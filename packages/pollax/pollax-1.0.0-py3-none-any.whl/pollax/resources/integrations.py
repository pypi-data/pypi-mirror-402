"""Integrations resource"""

from typing import List, TYPE_CHECKING
from ..models import Integration

if TYPE_CHECKING:
    from ..client import Pollax


class IntegrationsResource:
    """Integrations API resource"""

    def __init__(self, client: "Pollax"):
        self._client = client

    def create(self, name: str, integration_type: str, config: dict) -> Integration:
        """Create a new integration."""
        response = self._client.request(
            "POST",
            "/api/v1/integrations",
            json={"name": name, "type": integration_type, "config": config},
        )
        return Integration(**response)

    def list(self) -> List[Integration]:
        """List all integrations."""
        response = self._client.request("GET", "/api/v1/integrations")
        return [Integration(**item) for item in response]

    def retrieve(self, integration_id: str) -> Integration:
        """Get a single integration by ID."""
        response = self._client.request("GET", f"/api/v1/integrations/{integration_id}")
        return Integration(**response)

    def delete(self, integration_id: str) -> dict:
        """Delete an integration."""
        return self._client.request("DELETE", f"/api/v1/integrations/{integration_id}")
