"""Calls resource"""

from typing import List, Optional, TYPE_CHECKING
from ..models import Call

if TYPE_CHECKING:
    from ..client import Pollax


class CallsResource:
    """Calls API resource"""

    def __init__(self, client: "Pollax"):
        self._client = client

    def create(
        self,
        agent_id: str,
        to_number: str,
        from_number: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Call:
        """Create a new voice call."""
        data = {
            "agent_id": agent_id,
            "to_number": to_number,
            "from_number": from_number,
            "metadata": metadata or {},
        }
        response = self._client.request("POST", "/api/v1/calls", json=data)
        return Call(**response)

    def list(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Call]:
        """List all calls."""
        params = {"skip": skip, "limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        if status:
            params["status"] = status

        response = self._client.request("GET", "/api/v1/calls", params=params)
        return [Call(**item) for item in response]

    def retrieve(self, call_sid: str) -> Call:
        """Get a single call by SID."""
        response = self._client.request("GET", f"/api/v1/calls/{call_sid}")
        return Call(**response)

    def end(self, call_sid: str) -> Call:
        """End an active call."""
        response = self._client.request("POST", f"/api/v1/calls/{call_sid}/end")
        return Call(**response)

    def transfer(self, call_sid: str, to_number: str) -> Call:
        """Transfer a call to another number."""
        response = self._client.request(
            "POST",
            f"/api/v1/calls/{call_sid}/transfer",
            json={"to_number": to_number},
        )
        return Call(**response)

    def get_transcript(self, call_sid: str) -> dict:
        """Get call transcript."""
        return self._client.request("GET", f"/api/v1/calls/{call_sid}/transcript")

    def get_recording(self, call_sid: str) -> dict:
        """Get call recording URL."""
        return self._client.request("GET", f"/api/v1/calls/{call_sid}/recording")
