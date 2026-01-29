"""Agents resource"""

from typing import List, Optional, TYPE_CHECKING
from ..models import Agent

if TYPE_CHECKING:
    from ..client import Pollax


class AgentsResource:
    """Agents API resource"""

    def __init__(self, client: "Pollax"):
        self._client = client

    def create(
        self,
        name: str,
        system_prompt: str,
        description: Optional[str] = None,
        provider: str = "openai",
        model: str = "gpt-4",
        voice_provider: Optional[str] = None,
        voice_id: Optional[str] = None,
        stt_provider: str = "deepgram",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        config: Optional[dict] = None,
    ) -> Agent:
        """
        Create a new AI agent.
        
        Args:
            name: Agent name
            system_prompt: System prompt for the agent
            description: Agent description
            provider: LLM provider (openai, anthropic, ollama)
            model: Model name
            voice_provider: Voice provider (elevenlabs, openai, google)
            voice_id: Voice ID
            stt_provider: Speech-to-text provider
            temperature: Model temperature
            max_tokens: Maximum tokens
            config: Additional configuration
        
        Returns:
            Created agent
        
        Example:
            >>> agent = client.agents.create(
            ...     name="Support Agent",
            ...     system_prompt="You are helpful",
            ...     voice_id="alloy",
            ... )
        """
        data = {
            "name": name,
            "system_prompt": system_prompt,
            "description": description,
            "provider": provider,
            "model": model,
            "voice_provider": voice_provider,
            "voice_id": voice_id,
            "stt_provider": stt_provider,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "config": config,
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client.request("POST", "/api/v1/agents", json=data)
        return Agent(**response)

    def list(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Agent]:
        """
        List all agents.
        
        Args:
            is_active: Filter by active status
            skip: Number of agents to skip
            limit: Maximum number of agents to return
        
        Returns:
            List of agents
        
        Example:
            >>> agents = client.agents.list(is_active=True)
        """
        params = {"skip": skip, "limit": limit}
        if is_active is not None:
            params["is_active"] = is_active

        response = self._client.request("GET", "/api/v1/agents", params=params)
        return [Agent(**item) for item in response]

    def retrieve(self, agent_id: str) -> Agent:
        """
        Get a single agent by ID.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Agent
        
        Example:
            >>> agent = client.agents.retrieve("agent_123")
        """
        response = self._client.request("GET", f"/api/v1/agents/{agent_id}")
        return Agent(**response)

    def update(
        self,
        agent_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        is_active: Optional[bool] = None,
        **kwargs,
    ) -> Agent:
        """
        Update an agent.
        
        Args:
            agent_id: Agent ID
            name: New agent name
            description: New description
            system_prompt: New system prompt
            is_active: Active status
            **kwargs: Additional fields to update
        
        Returns:
            Updated agent
        
        Example:
            >>> agent = client.agents.update(
            ...     "agent_123",
            ...     name="New Name",
            ...     is_active=False,
            ... )
        """
        data = {
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "is_active": is_active,
            **kwargs,
        }
        data = {k: v for k, v in data.items() if v is not None}

        response = self._client.request("PUT", f"/api/v1/agents/{agent_id}", json=data)
        return Agent(**response)

    def delete(self, agent_id: str) -> dict:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Success response
        
        Example:
            >>> client.agents.delete("agent_123")
        """
        return self._client.request("DELETE", f"/api/v1/agents/{agent_id}")

    def test(self, agent_id: str, message: str) -> dict:
        """
        Test an agent with a sample message.
        
        Args:
            agent_id: Agent ID
            message: Test message
        
        Returns:
            Agent response
        
        Example:
            >>> response = client.agents.test(
            ...     "agent_123",
            ...     "Hello, how can you help?",
            ... )
        """
        return self._client.request(
            "POST",
            f"/api/v1/agents/{agent_id}/test",
            json={"message": message},
        )
