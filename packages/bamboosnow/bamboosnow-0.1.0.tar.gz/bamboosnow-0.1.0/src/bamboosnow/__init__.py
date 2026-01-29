"""
BambooSnow Python SDK

Official Python SDK for the BambooSnow AI agent automation platform.

Example:
    >>> from bamboosnow import BambooSnowClient
    >>>
    >>> # Using environment variable BAMBOOSNOW_API_KEY
    >>> client = BambooSnowClient()
    >>>
    >>> # Or pass the API key directly
    >>> client = BambooSnowClient(api_key="bs_...")
    >>>
    >>> # List your agents
    >>> agents = client.agents.list()
    >>>
    >>> # Get a specific run
    >>> run = client.runs.get("run_abc123")
    >>>
    >>> # Approve a pending action
    >>> client.runs.approve("run_abc123", approved=True)
"""

from bamboosnow.client import AsyncBambooSnowClient, BambooSnowClient
from bamboosnow.errors import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from bamboosnow.types import (
    Agent,
    AgentRun,
    AgentStatus,
    AgentTemplate,
    Analysis,
    PaginatedResponse,
    Repository,
    RunStatus,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "BambooSnowClient",
    "AsyncBambooSnowClient",
    # Errors
    "APIError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    # Types
    "Agent",
    "AgentRun",
    "AgentStatus",
    "AgentTemplate",
    "Analysis",
    "PaginatedResponse",
    "Repository",
    "RunStatus",
]
