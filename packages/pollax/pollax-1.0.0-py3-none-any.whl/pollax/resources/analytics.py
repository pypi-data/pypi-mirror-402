"""Analytics resource"""

from typing import Optional, TYPE_CHECKING
from ..models import DashboardStats

if TYPE_CHECKING:
    from ..client import Pollax


class AnalyticsResource:
    """Analytics API resource"""

    def __init__(self, client: "Pollax"):
        self._client = client

    def get_stats(self) -> DashboardStats:
        """Get dashboard statistics."""
        response = self._client.request("GET", "/api/v1/analytics/stats")
        return DashboardStats(**response)

    def get_call_volume(self, period: str = "7d") -> dict:
        """Get call volume over time."""
        return self._client.request("GET", "/api/v1/analytics/call-volume", params={"period": period})

    def get_agent_performance(self, agent_id: str) -> dict:
        """Get agent performance metrics."""
        return self._client.request("GET", f"/api/v1/analytics/agents/{agent_id}/performance")

    def export(self, start_date: str, end_date: str, format: str = "csv") -> dict:
        """Export analytics data."""
        return self._client.request(
            "GET",
            "/api/v1/analytics/export",
            params={"start_date": start_date, "end_date": end_date, "format": format},
        )
