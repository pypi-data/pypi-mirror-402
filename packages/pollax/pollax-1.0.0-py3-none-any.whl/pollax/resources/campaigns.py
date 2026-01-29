"""Campaigns resource"""

from typing import List, Optional, TYPE_CHECKING
from ..models import Campaign, Contact

if TYPE_CHECKING:
    from ..client import Pollax


class CampaignsResource:
    """Campaigns API resource"""

    def __init__(self, client: "Pollax"):
        self._client = client

    def create(
        self,
        name: str,
        agent_id: Optional[str] = None,
        scheduled_time: Optional[str] = None,
        contacts: Optional[List[dict]] = None,
    ) -> Campaign:
        """Create a new campaign."""
        data = {
            "name": name,
            "agent_id": agent_id,
            "scheduled_time": scheduled_time,
            "contacts": contacts or [],
        }
        response = self._client.request("POST", "/api/v1/campaigns", json=data)
        return Campaign(**response)

    def list(self) -> List[Campaign]:
        """List all campaigns."""
        response = self._client.request("GET", "/api/v1/campaigns")
        return [Campaign(**item) for item in response]

    def retrieve(self, campaign_id: str) -> Campaign:
        """Get a single campaign by ID."""
        response = self._client.request("GET", f"/api/v1/campaigns/{campaign_id}")
        return Campaign(**response)

    def update(self, campaign_id: str, **kwargs) -> Campaign:
        """Update a campaign."""
        response = self._client.request("PUT", f"/api/v1/campaigns/{campaign_id}", json=kwargs)
        return Campaign(**response)

    def delete(self, campaign_id: str) -> dict:
        """Delete a campaign."""
        return self._client.request("DELETE", f"/api/v1/campaigns/{campaign_id}")

    def start(self, campaign_id: str) -> Campaign:
        """Start a campaign."""
        response = self._client.request("POST", f"/api/v1/campaigns/{campaign_id}/start")
        return Campaign(**response)

    def pause(self, campaign_id: str) -> Campaign:
        """Pause a running campaign."""
        response = self._client.request("POST", f"/api/v1/campaigns/{campaign_id}/pause")
        return Campaign(**response)

    def get_stats(self, campaign_id: str) -> dict:
        """Get campaign statistics."""
        return self._client.request("GET", f"/api/v1/campaigns/{campaign_id}/stats")
