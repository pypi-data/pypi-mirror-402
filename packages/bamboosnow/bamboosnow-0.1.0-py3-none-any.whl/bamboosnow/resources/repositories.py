"""
Repositories Resource

Resource for managing connected repositories.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable

from bamboosnow.http import AsyncHttpClient, HttpClient
from bamboosnow.types import (
    Analysis,
    AnalysisStatus,
    PaginatedResponse,
    Repository,
)


class RepositoriesResource:
    """
    Resource for managing connected repositories.

    Example:
        >>> # List connected repositories
        >>> repos = client.repositories.list()
        >>>
        >>> # Connect a new repository
        >>> repo = client.repositories.connect(
        ...     provider="github",
        ...     full_name="myorg/myrepo",
        ... )
        >>>
        >>> # Run analysis
        >>> analysis = client.repositories.analyze(repository_id=repo.id)
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        provider: str | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[Repository]:
        """
        List connected repositories.

        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page
            provider: Filter by provider (e.g., "github")
            search: Search by repository name

        Returns:
            Paginated list of repositories
        """
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if provider is not None:
            params["provider"] = provider
        if search is not None:
            params["search"] = search

        data = self._http.get("/api/v1/repositories", params=params or None)
        items = [Repository.model_validate(item) for item in data["items"]]
        return PaginatedResponse[Repository](
            items=items,
            total=data["total"],
            page=data["page"],
            perPage=data["perPage"],
            totalPages=data["totalPages"],
        )

    def get(self, repository_id: str) -> Repository:
        """
        Get a specific repository.

        Args:
            repository_id: The repository ID

        Returns:
            The repository details
        """
        data = self._http.get(f"/api/v1/repositories/{repository_id}")
        return Repository.model_validate(data)

    def connect(
        self,
        *,
        provider: str,
        full_name: str,
    ) -> Repository:
        """
        Connect a new repository.

        Args:
            provider: The provider (e.g., "github")
            full_name: Full repository name (e.g., "myorg/myrepo")

        Returns:
            The connected repository
        """
        body = {"provider": provider, "fullName": full_name}
        data = self._http.post("/api/v1/repositories", json=body)
        return Repository.model_validate(data)

    def disconnect(self, repository_id: str) -> None:
        """
        Disconnect a repository.

        Args:
            repository_id: The repository ID
        """
        self._http.delete(f"/api/v1/repositories/{repository_id}")

    def sync(self, repository_id: str) -> Repository:
        """
        Sync repository metadata from the provider.

        Args:
            repository_id: The repository ID

        Returns:
            The updated repository
        """
        data = self._http.post(f"/api/v1/repositories/{repository_id}/sync")
        return Repository.model_validate(data)

    def analyze(
        self,
        repository_id: str,
        *,
        force: bool = False,
    ) -> Analysis:
        """
        Run analysis on a repository.

        Args:
            repository_id: The repository ID
            force: Force re-analysis even if recent analysis exists

        Returns:
            The created analysis
        """
        body = {"repositoryId": repository_id, "force": force}
        data = self._http.post("/api/v1/analysis", json=body)
        return Analysis.model_validate(data)

    def get_latest_analysis(self, repository_id: str) -> Analysis | None:
        """
        Get the latest analysis for a repository.

        Args:
            repository_id: The repository ID

        Returns:
            The latest analysis or None if none exists
        """
        from bamboosnow.errors import NotFoundError

        try:
            data = self._http.get(f"/api/v1/repositories/{repository_id}/analysis")
            return Analysis.model_validate(data)
        except NotFoundError:
            return None

    def list_analyses(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        repository_id: str | None = None,
        status: AnalysisStatus | str | None = None,
    ) -> PaginatedResponse[Analysis]:
        """
        List analyses.

        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page
            repository_id: Filter by repository
            status: Filter by analysis status

        Returns:
            Paginated list of analyses
        """
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if repository_id is not None:
            params["repository_id"] = repository_id
        if status is not None:
            params["status"] = status.value if isinstance(status, AnalysisStatus) else status

        data = self._http.get("/api/v1/analysis", params=params or None)
        items = [Analysis.model_validate(item) for item in data["items"]]
        return PaginatedResponse[Analysis](
            items=items,
            total=data["total"],
            page=data["page"],
            perPage=data["perPage"],
            totalPages=data["totalPages"],
        )

    def get_analysis(self, analysis_id: str) -> Analysis:
        """
        Get a specific analysis.

        Args:
            analysis_id: The analysis ID

        Returns:
            The analysis details
        """
        data = self._http.get(f"/api/v1/analysis/{analysis_id}")
        return Analysis.model_validate(data)

    def wait_for_analysis(
        self,
        analysis_id: str,
        *,
        interval_seconds: float = 2.0,
        timeout_seconds: float = 300.0,
        on_progress: Callable[[Analysis], None] | None = None,
    ) -> Analysis:
        """
        Wait for analysis to complete.

        Args:
            analysis_id: The analysis ID
            interval_seconds: Polling interval in seconds
            timeout_seconds: Timeout in seconds
            on_progress: Optional callback for progress updates

        Returns:
            The completed analysis

        Raises:
            TimeoutError: If the analysis doesn't complete within the timeout
        """
        terminal_states = {"completed", "failed"}
        start_time = time.time()

        while True:
            analysis = self.get_analysis(analysis_id)

            if on_progress:
                on_progress(analysis)

            if analysis.status.value in terminal_states:
                return analysis

            if time.time() - start_time > timeout_seconds:
                raise TimeoutError(f"Timeout waiting for analysis {analysis_id} to complete")

            time.sleep(interval_seconds)


class AsyncRepositoriesResource:
    """Async resource for managing connected repositories."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        provider: str | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[Repository]:
        """List connected repositories."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if provider is not None:
            params["provider"] = provider
        if search is not None:
            params["search"] = search

        data = await self._http.get("/api/v1/repositories", params=params or None)
        items = [Repository.model_validate(item) for item in data["items"]]
        return PaginatedResponse[Repository](
            items=items,
            total=data["total"],
            page=data["page"],
            perPage=data["perPage"],
            totalPages=data["totalPages"],
        )

    async def get(self, repository_id: str) -> Repository:
        """Get a specific repository."""
        data = await self._http.get(f"/api/v1/repositories/{repository_id}")
        return Repository.model_validate(data)

    async def connect(
        self,
        *,
        provider: str,
        full_name: str,
    ) -> Repository:
        """Connect a new repository."""
        body = {"provider": provider, "fullName": full_name}
        data = await self._http.post("/api/v1/repositories", json=body)
        return Repository.model_validate(data)

    async def disconnect(self, repository_id: str) -> None:
        """Disconnect a repository."""
        await self._http.delete(f"/api/v1/repositories/{repository_id}")

    async def sync(self, repository_id: str) -> Repository:
        """Sync repository metadata from the provider."""
        data = await self._http.post(f"/api/v1/repositories/{repository_id}/sync")
        return Repository.model_validate(data)

    async def analyze(
        self,
        repository_id: str,
        *,
        force: bool = False,
    ) -> Analysis:
        """Run analysis on a repository."""
        body = {"repositoryId": repository_id, "force": force}
        data = await self._http.post("/api/v1/analysis", json=body)
        return Analysis.model_validate(data)

    async def get_latest_analysis(self, repository_id: str) -> Analysis | None:
        """Get the latest analysis for a repository."""
        from bamboosnow.errors import NotFoundError

        try:
            data = await self._http.get(f"/api/v1/repositories/{repository_id}/analysis")
            return Analysis.model_validate(data)
        except NotFoundError:
            return None

    async def list_analyses(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        repository_id: str | None = None,
        status: AnalysisStatus | str | None = None,
    ) -> PaginatedResponse[Analysis]:
        """List analyses."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if repository_id is not None:
            params["repository_id"] = repository_id
        if status is not None:
            params["status"] = status.value if isinstance(status, AnalysisStatus) else status

        data = await self._http.get("/api/v1/analysis", params=params or None)
        items = [Analysis.model_validate(item) for item in data["items"]]
        return PaginatedResponse[Analysis](
            items=items,
            total=data["total"],
            page=data["page"],
            perPage=data["perPage"],
            totalPages=data["totalPages"],
        )

    async def get_analysis(self, analysis_id: str) -> Analysis:
        """Get a specific analysis."""
        data = await self._http.get(f"/api/v1/analysis/{analysis_id}")
        return Analysis.model_validate(data)

    async def wait_for_analysis(
        self,
        analysis_id: str,
        *,
        interval_seconds: float = 2.0,
        timeout_seconds: float = 300.0,
        on_progress: Callable[[Analysis], None] | None = None,
    ) -> Analysis:
        """Wait for analysis to complete."""
        terminal_states = {"completed", "failed"}
        start_time = time.time()

        while True:
            analysis = await self.get_analysis(analysis_id)

            if on_progress:
                on_progress(analysis)

            if analysis.status.value in terminal_states:
                return analysis

            if time.time() - start_time > timeout_seconds:
                raise TimeoutError(f"Timeout waiting for analysis {analysis_id} to complete")

            await asyncio.sleep(interval_seconds)
