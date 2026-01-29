"""Resource modules"""

from .agents import AgentsResource
from .calls import CallsResource
from .campaigns import CampaignsResource
from .knowledge import KnowledgeResource
from .analytics import AnalyticsResource
from .integrations import IntegrationsResource
from .phone_numbers import PhoneNumbersResource
from .api_keys import ApiKeysResource
from .voice_cloning import VoiceCloningResource

__all__ = [
    "AgentsResource",
    "CallsResource",
    "CampaignsResource",
    "KnowledgeResource",
    "AnalyticsResource",
    "IntegrationsResource",
    "PhoneNumbersResource",
    "ApiKeysResource",
    "VoiceCloningResource",
]
