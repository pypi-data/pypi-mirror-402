"""
Agents Resource

Resource for managing AI agents.
"""

from __future__ import annotations

from typing import Any

from bamboosnow.http import AsyncHttpClient, HttpClient
from bamboosnow.types import (
    Agent,
    AgentHealthScore,
    AgentStatus,
    AgentTemplate,
    PaginatedResponse,
)


class AgentsResource:
    """
    Resource for managing AI agents.

    Example:
        >>> # List all agents
        >>> agents = client.agents.list()
        >>>
        >>> # Get a specific agent
        >>> agent = client.agents.get("agt_abc123")
        >>>
        >>> # Pause an agent
        >>> client.agents.pause("agt_abc123")
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        status: AgentStatus | str | None = None,
        repository_id: str | None = None,
        project_id: str | None = None,
    ) -> PaginatedResponse[Agent]:
        """
        List all agents.

        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page
            status: Filter by agent status
            repository_id: Filter by repository
            project_id: Filter by project

        Returns:
            Paginated list of agents
        """
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if status is not None:
            params["status"] = status.value if isinstance(status, AgentStatus) else status
        if repository_id is not None:
            params["repository_id"] = repository_id
        if project_id is not None:
            params["project_id"] = project_id

        data = self._http.get("/api/v1/agents", params=params or None)
        items = [Agent.model_validate(item) for item in data["items"]]
        return PaginatedResponse[Agent](
            items=items,
            total=data["total"],
            page=data["page"],
            perPage=data["perPage"],
            totalPages=data["totalPages"],
        )

    def get(self, agent_id: str) -> Agent:
        """
        Get a specific agent by ID.

        Args:
            agent_id: The agent ID

        Returns:
            The agent details
        """
        data = self._http.get(f"/api/v1/agents/{agent_id}")
        return Agent.model_validate(data)

    def update(
        self,
        agent_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        triggers: list[str] | None = None,
    ) -> Agent:
        """
        Update an agent's configuration.

        Args:
            agent_id: The agent ID
            name: New name for the agent
            description: New description
            triggers: New trigger configuration

        Returns:
            The updated agent
        """
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if triggers is not None:
            body["triggers"] = triggers

        data = self._http.patch(f"/api/v1/agents/{agent_id}", json=body)
        return Agent.model_validate(data)

    def delete(self, agent_id: str) -> None:
        """
        Delete an agent.

        Args:
            agent_id: The agent ID
        """
        self._http.delete(f"/api/v1/agents/{agent_id}")

    def pause(self, agent_id: str) -> Agent:
        """
        Pause a deployed agent.

        Paused agents will not respond to triggers until resumed.

        Args:
            agent_id: The agent ID

        Returns:
            The updated agent
        """
        data = self._http.post(f"/api/v1/agents/{agent_id}/pause")
        return Agent.model_validate(data)

    def resume(self, agent_id: str) -> Agent:
        """
        Resume a paused agent.

        Args:
            agent_id: The agent ID

        Returns:
            The updated agent
        """
        data = self._http.post(f"/api/v1/agents/{agent_id}/resume")
        return Agent.model_validate(data)

    def archive(self, agent_id: str) -> Agent:
        """
        Archive an agent.

        Archived agents are kept for historical purposes but cannot be resumed.

        Args:
            agent_id: The agent ID

        Returns:
            The updated agent
        """
        data = self._http.post(f"/api/v1/agents/{agent_id}/archive")
        return Agent.model_validate(data)

    def list_templates(self) -> list[AgentTemplate]:
        """
        List available agent templates.

        Returns:
            List of agent templates
        """
        data = self._http.get("/api/v1/agents/templates")
        return [AgentTemplate.model_validate(item) for item in data]

    def get_template(self, slug: str) -> AgentTemplate:
        """
        Get a specific agent template.

        Args:
            slug: The template slug

        Returns:
            The template details
        """
        data = self._http.get(f"/api/v1/agents/templates/{slug}")
        return AgentTemplate.model_validate(data)

    def get_health(self, agent_id: str) -> AgentHealthScore:
        """
        Get health score for an agent.

        Args:
            agent_id: The agent ID

        Returns:
            Health score breakdown
        """
        data = self._http.get(f"/api/v1/agents/{agent_id}/health")
        return AgentHealthScore.model_validate(data)

    def trigger(
        self,
        agent_id: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """
        Trigger an agent run manually.

        Args:
            agent_id: The agent ID
            payload: Optional trigger payload

        Returns:
            Dict containing the created run ID
        """
        data = self._http.post(f"/api/v1/agents/{agent_id}/trigger", json=payload)
        return {"run_id": data["runId"]}


class AsyncAgentsResource:
    """Async resource for managing AI agents."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        status: AgentStatus | str | None = None,
        repository_id: str | None = None,
        project_id: str | None = None,
    ) -> PaginatedResponse[Agent]:
        """List all agents."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if status is not None:
            params["status"] = status.value if isinstance(status, AgentStatus) else status
        if repository_id is not None:
            params["repository_id"] = repository_id
        if project_id is not None:
            params["project_id"] = project_id

        data = await self._http.get("/api/v1/agents", params=params or None)
        items = [Agent.model_validate(item) for item in data["items"]]
        return PaginatedResponse[Agent](
            items=items,
            total=data["total"],
            page=data["page"],
            perPage=data["perPage"],
            totalPages=data["totalPages"],
        )

    async def get(self, agent_id: str) -> Agent:
        """Get a specific agent by ID."""
        data = await self._http.get(f"/api/v1/agents/{agent_id}")
        return Agent.model_validate(data)

    async def update(
        self,
        agent_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        triggers: list[str] | None = None,
    ) -> Agent:
        """Update an agent's configuration."""
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if triggers is not None:
            body["triggers"] = triggers

        data = await self._http.patch(f"/api/v1/agents/{agent_id}", json=body)
        return Agent.model_validate(data)

    async def delete(self, agent_id: str) -> None:
        """Delete an agent."""
        await self._http.delete(f"/api/v1/agents/{agent_id}")

    async def pause(self, agent_id: str) -> Agent:
        """Pause a deployed agent."""
        data = await self._http.post(f"/api/v1/agents/{agent_id}/pause")
        return Agent.model_validate(data)

    async def resume(self, agent_id: str) -> Agent:
        """Resume a paused agent."""
        data = await self._http.post(f"/api/v1/agents/{agent_id}/resume")
        return Agent.model_validate(data)

    async def archive(self, agent_id: str) -> Agent:
        """Archive an agent."""
        data = await self._http.post(f"/api/v1/agents/{agent_id}/archive")
        return Agent.model_validate(data)

    async def list_templates(self) -> list[AgentTemplate]:
        """List available agent templates."""
        data = await self._http.get("/api/v1/agents/templates")
        return [AgentTemplate.model_validate(item) for item in data]

    async def get_template(self, slug: str) -> AgentTemplate:
        """Get a specific agent template."""
        data = await self._http.get(f"/api/v1/agents/templates/{slug}")
        return AgentTemplate.model_validate(data)

    async def get_health(self, agent_id: str) -> AgentHealthScore:
        """Get health score for an agent."""
        data = await self._http.get(f"/api/v1/agents/{agent_id}/health")
        return AgentHealthScore.model_validate(data)

    async def trigger(
        self,
        agent_id: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Trigger an agent run manually."""
        data = await self._http.post(f"/api/v1/agents/{agent_id}/trigger", json=payload)
        return {"run_id": data["runId"]}
