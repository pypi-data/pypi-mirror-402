"""Phone numbers resource"""

from typing import List, Optional, TYPE_CHECKING
from ..models import PhoneNumber

if TYPE_CHECKING:
    from ..client import Pollax


class PhoneNumbersResource:
    """Phone Numbers API resource"""

    def __init__(self, client: "Pollax"):
        self._client = client

    def list(self) -> List[PhoneNumber]:
        """List all phone numbers."""
        response = self._client.request("GET", "/api/v1/phone-numbers")
        return [PhoneNumber(**item) for item in response]

    def search(
        self,
        country_code: Optional[str] = None,
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        limit: int = 10,
    ) -> List[PhoneNumber]:
        """Search available phone numbers."""
        params = {"limit": limit}
        if country_code:
            params["country_code"] = country_code
        if area_code:
            params["area_code"] = area_code
        if contains:
            params["contains"] = contains

        response = self._client.request("GET", "/api/v1/phone-numbers/search", params=params)
        return [PhoneNumber(**item) for item in response]

    def purchase(self, phone_number: str) -> PhoneNumber:
        """Purchase a phone number."""
        response = self._client.request(
            "POST",
            "/api/v1/phone-numbers",
            json={"phone_number": phone_number},
        )
        return PhoneNumber(**response)

    def release(self, number_id: str) -> dict:
        """Release a phone number."""
        return self._client.request("DELETE", f"/api/v1/phone-numbers/{number_id}")
