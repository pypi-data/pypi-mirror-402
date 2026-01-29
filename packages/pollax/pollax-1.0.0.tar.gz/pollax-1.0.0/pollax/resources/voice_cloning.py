"""Voice cloning resource"""

from typing import List, Optional, TYPE_CHECKING, BinaryIO
from ..models import VoiceProfile

if TYPE_CHECKING:
    from ..client import Pollax


class VoiceCloningResource:
    """Voice Cloning API resource"""

    def __init__(self, client: "Pollax"):
        self._client = client

    def create(
        self,
        name: str,
        audio_files: List[BinaryIO],
        description: Optional[str] = None,
        provider: str = "elevenlabs",
    ) -> VoiceProfile:
        """Create a new voice profile."""
        files = {f"audio_{i}": f for i, f in enumerate(audio_files)}
        data = {"name": name, "provider": provider}
        if description:
            data["description"] = description

        response = self._client.request("POST", "/api/v1/voice-cloning", files=files, params=data)
        return VoiceProfile(**response)

    def list(self) -> List[VoiceProfile]:
        """List all voice profiles."""
        response = self._client.request("GET", "/api/v1/voice-cloning")
        return [VoiceProfile(**item) for item in response]

    def retrieve(self, voice_id: str) -> VoiceProfile:
        """Get a single voice profile by ID."""
        response = self._client.request("GET", f"/api/v1/voice-cloning/{voice_id}")
        return VoiceProfile(**response)

    def delete(self, voice_id: str) -> dict:
        """Delete a voice profile."""
        return self._client.request("DELETE", f"/api/v1/voice-cloning/{voice_id}")
