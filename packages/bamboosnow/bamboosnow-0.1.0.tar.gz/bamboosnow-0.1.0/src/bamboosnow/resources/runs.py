"""
Runs Resource

Resource for monitoring and controlling agent runs.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable

from bamboosnow.http import AsyncHttpClient, HttpClient
from bamboosnow.types import (
    AgentRun,
    PaginatedResponse,
    RunStatus,
    RunSummary,
    ThoughtStep,
)


class RunsResource:
    """
    Resource for monitoring and controlling agent runs.

    Example:
        >>> # List recent runs
        >>> runs = client.runs.list()
        >>>
        >>> # Get a specific run
        >>> run = client.runs.get("run_abc123")
        >>>
        >>> # Approve a pending action
        >>> client.runs.approve("run_abc123", approved=True)
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        agent_id: str | None = None,
        status: RunStatus | str | None = None,
        trigger_type: str | None = None,
    ) -> PaginatedResponse[RunSummary]:
        """
        List agent runs.

        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page
            agent_id: Filter by agent
            status: Filter by run status
            trigger_type: Filter by trigger type

        Returns:
            Paginated list of runs
        """
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if agent_id is not None:
            params["agent_id"] = agent_id
        if status is not None:
            params["status"] = status.value if isinstance(status, RunStatus) else status
        if trigger_type is not None:
            params["trigger_type"] = trigger_type

        data = self._http.get("/api/v1/runs", params=params or None)
        items = [RunSummary.model_validate(item) for item in data["items"]]
        return PaginatedResponse[RunSummary](
            items=items,
            total=data["total"],
            page=data["page"],
            perPage=data["perPage"],
            totalPages=data["totalPages"],
        )

    def get(self, run_id: str) -> AgentRun:
        """
        Get a specific run by ID.

        Returns full run details including thought trace and actions.

        Args:
            run_id: The run ID

        Returns:
            The run details
        """
        data = self._http.get(f"/api/v1/runs/{run_id}")
        return AgentRun.model_validate(data)

    def get_thought_trace(self, run_id: str) -> list[ThoughtStep]:
        """
        Get just the thought trace for a run.

        Use this for polling updates without fetching the full run.

        Args:
            run_id: The run ID

        Returns:
            List of thought steps
        """
        data = self._http.get(f"/api/v1/runs/{run_id}/trace")
        return [ThoughtStep.model_validate(item) for item in data]

    def get_logs(self, run_id: str) -> str:
        """
        Get the logs for a run (formatted thought trace).

        Args:
            run_id: The run ID

        Returns:
            Formatted log string
        """
        return self._http.get(f"/api/v1/runs/{run_id}/logs")

    def approve(
        self,
        run_id: str,
        *,
        approved: bool,
        comment: str | None = None,
    ) -> AgentRun:
        """
        Approve or reject a pending action.

        When an agent requires human approval (human-in-the-loop),
        use this to approve or reject the pending action.

        Args:
            run_id: The run ID
            approved: Whether to approve the action
            comment: Optional comment

        Returns:
            The updated run
        """
        body: dict[str, Any] = {"approved": approved}
        if comment is not None:
            body["comment"] = comment

        data = self._http.post(f"/api/v1/runs/{run_id}/approve", json=body)
        return AgentRun.model_validate(data)

    def cancel(
        self,
        run_id: str,
        *,
        reason: str | None = None,
    ) -> AgentRun:
        """
        Cancel a running or queued job.

        Args:
            run_id: The run ID
            reason: Optional cancellation reason

        Returns:
            The updated run
        """
        body: dict[str, Any] = {}
        if reason is not None:
            body["reason"] = reason

        data = self._http.post(f"/api/v1/runs/{run_id}/cancel", json=body or None)
        return AgentRun.model_validate(data)

    def retry(self, run_id: str) -> AgentRun:
        """
        Retry a failed run.

        Creates a new run with the same trigger payload.

        Args:
            run_id: The run ID to retry

        Returns:
            The new run
        """
        data = self._http.post(f"/api/v1/runs/{run_id}/retry")
        return AgentRun.model_validate(data)

    def wait_for_completion(
        self,
        run_id: str,
        *,
        interval_seconds: float = 2.0,
        timeout_seconds: float = 300.0,
        on_progress: Callable[[AgentRun], None] | None = None,
    ) -> AgentRun:
        """
        Poll for run completion.

        Waits for a run to reach a terminal state (completed, failed, or cancelled).

        Args:
            run_id: The run ID
            interval_seconds: Polling interval in seconds
            timeout_seconds: Timeout in seconds
            on_progress: Optional callback for progress updates

        Returns:
            The final run state

        Raises:
            TimeoutError: If the run doesn't complete within the timeout
        """
        terminal_states = {"completed", "failed", "cancelled"}
        start_time = time.time()

        while True:
            run = self.get(run_id)

            if on_progress:
                on_progress(run)

            if run.status.value in terminal_states:
                return run

            if time.time() - start_time > timeout_seconds:
                raise TimeoutError(f"Timeout waiting for run {run_id} to complete")

            time.sleep(interval_seconds)

    def get_pending_approvals(self) -> PaginatedResponse[RunSummary]:
        """
        Get runs requiring approval.

        Convenience method to list runs waiting for human approval.

        Returns:
            Paginated list of runs waiting for approval
        """
        return self.list(status=RunStatus.WAITING_APPROVAL)


class AsyncRunsResource:
    """Async resource for monitoring and controlling agent runs."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        agent_id: str | None = None,
        status: RunStatus | str | None = None,
        trigger_type: str | None = None,
    ) -> PaginatedResponse[RunSummary]:
        """List agent runs."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if agent_id is not None:
            params["agent_id"] = agent_id
        if status is not None:
            params["status"] = status.value if isinstance(status, RunStatus) else status
        if trigger_type is not None:
            params["trigger_type"] = trigger_type

        data = await self._http.get("/api/v1/runs", params=params or None)
        items = [RunSummary.model_validate(item) for item in data["items"]]
        return PaginatedResponse[RunSummary](
            items=items,
            total=data["total"],
            page=data["page"],
            perPage=data["perPage"],
            totalPages=data["totalPages"],
        )

    async def get(self, run_id: str) -> AgentRun:
        """Get a specific run by ID."""
        data = await self._http.get(f"/api/v1/runs/{run_id}")
        return AgentRun.model_validate(data)

    async def get_thought_trace(self, run_id: str) -> list[ThoughtStep]:
        """Get just the thought trace for a run."""
        data = await self._http.get(f"/api/v1/runs/{run_id}/trace")
        return [ThoughtStep.model_validate(item) for item in data]

    async def get_logs(self, run_id: str) -> str:
        """Get the logs for a run."""
        return await self._http.get(f"/api/v1/runs/{run_id}/logs")

    async def approve(
        self,
        run_id: str,
        *,
        approved: bool,
        comment: str | None = None,
    ) -> AgentRun:
        """Approve or reject a pending action."""
        body: dict[str, Any] = {"approved": approved}
        if comment is not None:
            body["comment"] = comment

        data = await self._http.post(f"/api/v1/runs/{run_id}/approve", json=body)
        return AgentRun.model_validate(data)

    async def cancel(
        self,
        run_id: str,
        *,
        reason: str | None = None,
    ) -> AgentRun:
        """Cancel a running or queued job."""
        body: dict[str, Any] = {}
        if reason is not None:
            body["reason"] = reason

        data = await self._http.post(f"/api/v1/runs/{run_id}/cancel", json=body or None)
        return AgentRun.model_validate(data)

    async def retry(self, run_id: str) -> AgentRun:
        """Retry a failed run."""
        data = await self._http.post(f"/api/v1/runs/{run_id}/retry")
        return AgentRun.model_validate(data)

    async def wait_for_completion(
        self,
        run_id: str,
        *,
        interval_seconds: float = 2.0,
        timeout_seconds: float = 300.0,
        on_progress: Callable[[AgentRun], None] | None = None,
    ) -> AgentRun:
        """Poll for run completion."""
        terminal_states = {"completed", "failed", "cancelled"}
        start_time = time.time()

        while True:
            run = await self.get(run_id)

            if on_progress:
                on_progress(run)

            if run.status.value in terminal_states:
                return run

            if time.time() - start_time > timeout_seconds:
                raise TimeoutError(f"Timeout waiting for run {run_id} to complete")

            await asyncio.sleep(interval_seconds)

    async def get_pending_approvals(self) -> PaginatedResponse[RunSummary]:
        """Get runs requiring approval."""
        return await self.list(status=RunStatus.WAITING_APPROVAL)
