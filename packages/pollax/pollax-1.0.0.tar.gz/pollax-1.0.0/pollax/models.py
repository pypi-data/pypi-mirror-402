"""Pydantic models for Pollax API"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class Agent(BaseModel):
    """AI Agent model"""

    id: str
    name: str
    description: Optional[str] = None
    system_prompt: str
    provider: Literal["openai", "anthropic", "ollama"] = "openai"
    model: str = "gpt-4"
    voice_provider: Optional[Literal["elevenlabs", "openai", "google"]] = None
    voice_id: Optional[str] = None
    stt_provider: Optional[Literal["deepgram", "whisper", "google"]] = "deepgram"
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_active: bool = True
    tenant_id: str
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    calls_count: Optional[int] = None
    success_rate: Optional[str] = None
    avg_duration: Optional[str] = None


class Call(BaseModel):
    """Voice call model"""

    call_sid: str
    agent_id: str
    to_number: str
    from_number: Optional[str] = None
    status: Literal["queued", "ringing", "in-progress", "completed", "failed", "busy", "no-answer"]
    direction: Literal["inbound", "outbound"]
    duration: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    agent_name: Optional[str] = None


class Contact(BaseModel):
    """Campaign contact model"""

    name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Campaign(BaseModel):
    """Campaign model"""

    id: str
    name: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    status: Literal["draft", "scheduled", "running", "paused", "completed", "cancelled"]
    scheduled_time: Optional[datetime] = None
    contacts: List[Contact] = Field(default_factory=list)
    total_contacts: int = 0
    completed_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    tenant_id: str
    created_at: datetime
    updated_at: datetime


class KnowledgeDocument(BaseModel):
    """Knowledge base document model"""

    id: str
    name: str
    type: Literal["pdf", "txt", "docx", "url"]
    content: Optional[str] = None
    url: Optional[str] = None
    chunks_count: int = 0
    status: Literal["processing", "ready", "failed"]
    tenant_id: str
    created_at: datetime


class DashboardStats(BaseModel):
    """Dashboard statistics model"""

    total_calls: int
    active_agents: int
    success_rate: str
    avg_duration: str
    calls_by_status: Dict[str, int]


class Integration(BaseModel):
    """Integration model"""

    id: str
    name: str
    type: Literal["twilio", "salesforce", "hubspot", "slack", "zapier", "webhook"]
    config: Dict[str, Any]
    is_active: bool
    tenant_id: str
    created_at: datetime
    updated_at: datetime


class PhoneNumber(BaseModel):
    """Phone number model"""

    id: str
    phone_number: str
    country_code: str
    capabilities: Dict[str, bool]
    is_active: bool
    tenant_id: str
    created_at: datetime


class ApiKey(BaseModel):
    """API key model"""

    id: str
    name: str
    key_prefix: str
    last_used_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime


class VoiceProfile(BaseModel):
    """Voice cloning profile model"""

    id: str
    name: str
    description: Optional[str] = None
    voice_id: str
    provider: Literal["elevenlabs", "openai"]
    status: Literal["training", "ready", "failed"]
    tenant_id: str
    created_at: datetime
