"""
BambooSnow SDK Client

The main entry point for interacting with the BambooSnow API.
"""

from __future__ import annotations

import os

from bamboosnow.http import AsyncHttpClient, HttpClient
from bamboosnow.resources.agents import AgentsResource, AsyncAgentsResource
from bamboosnow.resources.api_keys import APIKeysResource, AsyncAPIKeysResource
from bamboosnow.resources.repositories import AsyncRepositoriesResource, RepositoriesResource
from bamboosnow.resources.runs import AsyncRunsResource, RunsResource
from bamboosnow.resources.users import AsyncUsersResource, UsersResource

DEFAULT_BASE_URL = "https://api.bamboosnow.co"


class BambooSnowClient:
    """
    BambooSnow SDK Client

    The main entry point for interacting with the BambooSnow API.

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

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the BambooSnow client.

        Args:
            api_key: Your BambooSnow API key. Can also be set via:
                - BAMBOOSNOW_API_KEY environment variable
            base_url: Base URL for the BambooSnow API.
                Defaults to the production API.
                Can also be set via BAMBOOSNOW_BASE_URL environment variable.
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts for failed requests (default: 3)
        """
        self._api_key = self._resolve_api_key(api_key)
        self._base_url = self._resolve_base_url(base_url)

        self._http = HttpClient(
            base_url=self._base_url,
            api_key=self._api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Initialize resources
        self.agents = AgentsResource(self._http)
        self.runs = RunsResource(self._http)
        self.users = UsersResource(self._http)
        self.repositories = RepositoriesResource(self._http)
        self.api_keys = APIKeysResource(self._http)

    def _resolve_api_key(self, api_key: str | None) -> str | None:
        """Resolve API key from argument or environment."""
        if api_key:
            return api_key
        return os.environ.get("BAMBOOSNOW_API_KEY")

    def _resolve_base_url(self, base_url: str | None) -> str:
        """Resolve base URL from argument or environment."""
        if base_url:
            return base_url
        return os.environ.get("BAMBOOSNOW_BASE_URL", DEFAULT_BASE_URL)

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()

    def __enter__(self) -> "BambooSnowClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncBambooSnowClient:
    """
    Async BambooSnow SDK Client

    Async version of the BambooSnow client for use with asyncio.

    Example:
        >>> import asyncio
        >>> from bamboosnow import AsyncBambooSnowClient
        >>>
        >>> async def main():
        ...     async with AsyncBambooSnowClient() as client:
        ...         agents = await client.agents.list()
        ...         print(agents.items)
        >>>
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the async BambooSnow client.

        Args:
            api_key: Your BambooSnow API key. Can also be set via:
                - BAMBOOSNOW_API_KEY environment variable
            base_url: Base URL for the BambooSnow API.
                Defaults to the production API.
                Can also be set via BAMBOOSNOW_BASE_URL environment variable.
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts for failed requests (default: 3)
        """
        self._api_key = self._resolve_api_key(api_key)
        self._base_url = self._resolve_base_url(base_url)

        self._http = AsyncHttpClient(
            base_url=self._base_url,
            api_key=self._api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Initialize resources
        self.agents = AsyncAgentsResource(self._http)
        self.runs = AsyncRunsResource(self._http)
        self.users = AsyncUsersResource(self._http)
        self.repositories = AsyncRepositoriesResource(self._http)
        self.api_keys = AsyncAPIKeysResource(self._http)

    def _resolve_api_key(self, api_key: str | None) -> str | None:
        """Resolve API key from argument or environment."""
        if api_key:
            return api_key
        return os.environ.get("BAMBOOSNOW_API_KEY")

    def _resolve_base_url(self, base_url: str | None) -> str:
        """Resolve base URL from argument or environment."""
        if base_url:
            return base_url
        return os.environ.get("BAMBOOSNOW_BASE_URL", DEFAULT_BASE_URL)

    async def close(self) -> None:
        """Close the client and release resources."""
        await self._http.close()

    async def __aenter__(self) -> "AsyncBambooSnowClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
