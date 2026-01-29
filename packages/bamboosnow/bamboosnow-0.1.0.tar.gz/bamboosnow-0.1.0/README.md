# BambooSnow Python SDK

Official Python SDK for the [BambooSnow](https://bamboosnow.co) AI agent automation platform.

## Installation

```bash
pip install bamboosnow
```

## Quick Start

```python
from bamboosnow import BambooSnowClient

# Using environment variable BAMBOOSNOW_API_KEY
client = BambooSnowClient()

# Or pass the API key directly
client = BambooSnowClient(api_key="bs_...")

# List your agents
agents = client.agents.list()
for agent in agents.items:
    print(f"{agent.name}: {agent.status}")

# Get a specific run
run = client.runs.get("run_abc123")
print(f"Status: {run.status}, Tokens: {run.tokens_used}")

# Approve a pending action
client.runs.approve("run_abc123", approved=True, comment="Looks good!")
```

## Async Support

The SDK includes full async support:

```python
import asyncio
from bamboosnow import AsyncBambooSnowClient

async def main():
    async with AsyncBambooSnowClient() as client:
        agents = await client.agents.list()
        for agent in agents.items:
            print(f"{agent.name}: {agent.status}")

asyncio.run(main())
```

## Resources

### Agents

```python
# List agents
agents = client.agents.list(status="deployed")

# Get agent details
agent = client.agents.get("agt_abc123")

# Pause/resume agents
client.agents.pause("agt_abc123")
client.agents.resume("agt_abc123")

# Get agent health
health = client.agents.get_health("agt_abc123")
print(f"Grade: {health.grade}, Score: {health.overall_score}")

# Trigger a manual run
result = client.agents.trigger("agt_abc123", {"pr_number": 42})
print(f"Run ID: {result['run_id']}")

# List templates
templates = client.agents.list_templates()
```

### Runs

```python
# List runs
runs = client.runs.list(agent_id="agt_abc123")

# Get run details with thought trace
run = client.runs.get("run_abc123")
for step in run.thought_trace:
    print(f"[{step.type}] {step.content}")

# Approve/reject pending actions
client.runs.approve("run_abc123", approved=True)
client.runs.approve("run_abc123", approved=False, comment="Too risky")

# Cancel a running job
client.runs.cancel("run_abc123", reason="No longer needed")

# Wait for completion
run = client.runs.wait_for_completion(
    "run_abc123",
    on_progress=lambda r: print(f"Status: {r.status}")
)

# Get runs pending approval
pending = client.runs.get_pending_approvals()
```

### Repositories

```python
# List connected repos
repos = client.repositories.list()

# Connect a repository
repo = client.repositories.connect(
    provider="github",
    full_name="myorg/myrepo"
)

# Run analysis
analysis = client.repositories.analyze(repo.id)

# Wait for analysis to complete
analysis = client.repositories.wait_for_analysis(
    analysis.id,
    on_progress=lambda a: print(f"{a.progress_percent}% complete")
)

# Get latest analysis
latest = client.repositories.get_latest_analysis(repo.id)
```

### API Keys

```python
# List keys
keys = client.api_keys.list()

# Create a new key
result = client.api_keys.create(name="CI/CD Key")
print(f"Key: {result['key']}")  # Only shown once!

# Revoke a key
client.api_keys.revoke("key_abc123")
```

## Configuration

### Environment Variables

- `BAMBOOSNOW_API_KEY`: Your API key
- `BAMBOOSNOW_BASE_URL`: Custom API base URL (for self-hosted)

### Client Options

```python
client = BambooSnowClient(
    api_key="bs_...",
    base_url="https://api.bamboosnow.co",  # or self-hosted URL
    timeout=60.0,  # request timeout in seconds
    max_retries=3,  # retry attempts for failed requests
)
```

## Error Handling

```python
from bamboosnow import BambooSnowClient
from bamboosnow.errors import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

client = BambooSnowClient()

try:
    agent = client.agents.get("agt_abc123")
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Agent not found")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after} seconds")
except ValidationError as e:
    print(f"Validation error: {e.errors}")
except APIError as e:
    print(f"API error: {e.message}")
```

## Type Hints

The SDK is fully typed. All models are Pydantic v2 models with full IDE support:

```python
from bamboosnow import Agent, AgentStatus

def process_agent(agent: Agent) -> None:
    if agent.status == AgentStatus.DEPLOYED:
        print(f"{agent.name} is running")
```

## License

MIT
