# Pollax Python SDK

Official Python client library for the Pollax AI Voice Platform.

[![PyPI version](https://img.shields.io/pypi/v/pollax.svg)](https://pypi.org/project/pollax/)
[![Python Support](https://img.shields.io/pypi/pyversions/pollax.svg)](https://pypi.org/project/pollax/)
[![License](https://img.shields.io/pypi/l/pollax.svg)](https://github.com/pollax/pollax-python/blob/main/LICENSE)

## Installation

```bash
pip install pollax
```

## Quick Start

```python
from pollax import Pollax

# Initialize client
client = Pollax(api_key="sk_live_your_api_key_here")

# Create an AI agent
agent = client.agents.create(
    name="Customer Support Agent",
    system_prompt="You are a helpful customer support agent for Acme Corp.",
    voice_id="alloy",
    model="gpt-4",
)

# Make a call
call = client.calls.create(
    agent_id=agent.id,
    to_number="+1234567890",
    from_number="+0987654321",
)

print(f"Call initiated: {call.call_sid}")
```

## Features

- Full type hints with Pydantic models
- Async/await support
- Automatic retry logic with exponential backoff
- Comprehensive error handling
- Context manager support
- Python 3.8+ support

## Usage

### Client Initialization

```python
from pollax import Pollax

# Basic initialization
client = Pollax(api_key="sk_live_...")

# With custom configuration
client = Pollax(
    api_key="sk_live_...",
    base_url="https://api.pollax.ai",
    timeout=30.0,
    max_retries=3,
    tenant_id="org_123",
)

# Using context manager (recommended)
with Pollax(api_key="sk_live_...") as client:
    agents = client.agents.list()
```

### Agents

```python
# Create an agent
agent = client.agents.create(
    name="Support Agent",
    system_prompt="You are a helpful assistant",
    voice_provider="elevenlabs",
    voice_id="voice_abc123",
    model="gpt-4",
    temperature=0.7,
)

# List agents
agents = client.agents.list(is_active=True)

# Get a specific agent
agent = client.agents.retrieve("agent_123")

# Update an agent
agent = client.agents.update(
    "agent_123",
    name="New Name",
    is_active=False,
)

# Delete an agent
client.agents.delete("agent_123")

# Test an agent
response = client.agents.test("agent_123", "Hello, how can you help?")
print(response)
```

### Calls

```python
# Create a call
call = client.calls.create(
    agent_id="agent_123",
    to_number="+1234567890",
    from_number="+0987654321",
    metadata={"customer_id": "cust_456"},
)

# List calls
calls = client.calls.list(
    agent_id="agent_123",
    status="completed",
)

# Get call details
call = client.calls.retrieve("CA123456")

# End a call
client.calls.end("CA123456")

# Transfer a call
client.calls.transfer("CA123456", to_number="+1111111111")

# Get call transcript
transcript = client.calls.get_transcript("CA123456")
print(transcript)

# Get call recording
recording = client.calls.get_recording("CA123456")
print(recording["url"])
```

### Campaigns

```python
# Create a campaign
campaign = client.campaigns.create(
    name="Q1 Outreach Campaign",
    agent_id="agent_123",
    contacts=[
        {"name": "John Doe", "phone": "+1234567890"},
        {"name": "Jane Smith", "phone": "+0987654321"},
    ],
)

# Start campaign
client.campaigns.start("campaign_123")

# Pause campaign
client.campaigns.pause("campaign_123")

# Get campaign stats
stats = client.campaigns.get_stats("campaign_123")
print(f"Success rate: {stats['success_rate']}")
```

### Knowledge Base

```python
# Upload a document
with open("manual.pdf", "rb") as f:
    doc = client.knowledge.upload(
        name="Product Manual",
        file=f,
        doc_type="pdf",
    )

# Upload from text
doc = client.knowledge.upload(
    name="FAQ",
    content="Q: How do I reset my password? A: Click forgot password...",
    doc_type="txt",
)

# Search knowledge base
results = client.knowledge.search(
    query="How do I reset my password?",
    limit=5,
)

for result in results["results"]:
    print(f"Score: {result['score']}")
    print(f"Content: {result['content']}")

# Delete a document
client.knowledge.delete("doc_123")
```

### Analytics

```python
# Get dashboard statistics
stats = client.analytics.get_stats()
print(f"Total calls: {stats.total_calls}")
print(f"Active agents: {stats.active_agents}")
print(f"Success rate: {stats.success_rate}")

# Get call volume over time
volume = client.analytics.get_call_volume(period="7d")

# Get agent performance
performance = client.analytics.get_agent_performance("agent_123")

# Export data
data = client.analytics.export(
    start_date="2024-01-01",
    end_date="2024-01-31",
    format="csv",
)
```

### Integrations

```python
# Create an integration
integration = client.integrations.create(
    name="Salesforce CRM",
    integration_type="salesforce",
    config={
        "client_id": "...",
        "client_secret": "...",
    },
)

# List integrations
integrations = client.integrations.list()

# Delete integration
client.integrations.delete("int_123")
```

### Phone Numbers

```python
# Search available numbers
numbers = client.phone_numbers.search(
    country_code="US",
    area_code="415",
)

# Purchase a number
number = client.phone_numbers.purchase("+14155551234")

# Release a number
client.phone_numbers.release("num_123")
```

### Voice Cloning

```python
# Create a custom voice
with open("sample1.wav", "rb") as f1, open("sample2.wav", "rb") as f2:
    voice = client.voice_cloning.create(
        name="Custom Voice",
        description="My custom voice profile",
        audio_files=[f1, f2],
        provider="elevenlabs",
    )

# List voices
voices = client.voice_cloning.list()

# Delete voice
client.voice_cloning.delete("voice_123")
```

## Error Handling

```python
from pollax import (
    Pollax,
    PollaxError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)

client = Pollax(api_key="sk_live_...")

try:
    agent = client.agents.retrieve("agent_123")
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Agent not found")
except RateLimitError:
    print("Rate limit exceeded, try again later")
except PollaxError as e:
    print(f"API error: {e.message}")
    print(f"Status code: {e.status_code}")
```

## Type Safety

The SDK uses Pydantic for data validation and type safety:

```python
from pollax import Pollax
from pollax.models import Agent, Call

client = Pollax(api_key="sk_live_...")

# Full type hints
agent: Agent = client.agents.create(
    name="Support Agent",
    system_prompt="You are helpful",
    model="gpt-4",
)

# IDE autocomplete works perfectly
print(agent.id)
print(agent.name)
print(agent.created_at)
```

## Development

```bash
# Clone repository
git clone https://github.com/pollax/pollax-python
cd pollax-python

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black pollax tests

# Type checking
mypy pollax
```

## License

MIT

## Support

- 📧 Email: support@pollax.ai
- 💬 [Discord Community](https://discord.gg/pollax)
- 🐛 [Report Issues](https://github.com/pollax/pollax-python/issues)
- 📖 [Documentation](https://docs.pollax.ai)
