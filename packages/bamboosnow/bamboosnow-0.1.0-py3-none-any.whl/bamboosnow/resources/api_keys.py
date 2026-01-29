"""
API Keys Resource

Resource for managing API keys.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from bamboosnow.http import AsyncHttpClient, HttpClient
from bamboosnow.types import APIKey, PaginatedResponse


class APIKeysResource:
    """
    Resource for managing API keys.

    Example:
        >>> # List API keys
        >>> keys = client.api_keys.list()
        >>>
        >>> # Create a new key
        >>> result = client.api_keys.create(name="My Key")
        >>> print(result["key"])  # Only shown once!
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[APIKey]:
        """
        List API keys.

        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page

        Returns:
            Paginated list of API keys
        """
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page

        data = self._http.get("/api/v1/api-keys", params=params or None)
        items = [APIKey.model_validate(item) for item in data["items"]]
        return PaginatedResponse[APIKey](
            items=items,
            total=data["total"],
            page=data["page"],
            perPage=data["perPage"],
            totalPages=data["totalPages"],
        )

    def create(
        self,
        *,
        name: str,
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Create a new API key.

        Args:
            name: A name for the key
            expires_at: Optional expiration date

        Returns:
            Dict containing the key (only shown once!) and key metadata
        """
        body: dict[str, Any] = {"name": name}
        if expires_at is not None:
            body["expiresAt"] = expires_at.isoformat()

        return self._http.post("/api/v1/api-keys", json=body)

    def get(self, key_id: str) -> APIKey:
        """
        Get an API key by ID.

        Args:
            key_id: The API key ID

        Returns:
            The API key metadata (not the actual key value)
        """
        data = self._http.get(f"/api/v1/api-keys/{key_id}")
        return APIKey.model_validate(data)

    def delete(self, key_id: str) -> None:
        """
        Delete an API key.

        Args:
            key_id: The API key ID
        """
        self._http.delete(f"/api/v1/api-keys/{key_id}")

    def revoke(self, key_id: str) -> None:
        """
        Revoke an API key (alias for delete).

        Args:
            key_id: The API key ID
        """
        self.delete(key_id)


class AsyncAPIKeysResource:
    """Async resource for managing API keys."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[APIKey]:
        """List API keys."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page

        data = await self._http.get("/api/v1/api-keys", params=params or None)
        items = [APIKey.model_validate(item) for item in data["items"]]
        return PaginatedResponse[APIKey](
            items=items,
            total=data["total"],
            page=data["page"],
            perPage=data["perPage"],
            totalPages=data["totalPages"],
        )

    async def create(
        self,
        *,
        name: str,
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Create a new API key."""
        body: dict[str, Any] = {"name": name}
        if expires_at is not None:
            body["expiresAt"] = expires_at.isoformat()

        return await self._http.post("/api/v1/api-keys", json=body)

    async def get(self, key_id: str) -> APIKey:
        """Get an API key by ID."""
        data = await self._http.get(f"/api/v1/api-keys/{key_id}")
        return APIKey.model_validate(data)

    async def delete(self, key_id: str) -> None:
        """Delete an API key."""
        await self._http.delete(f"/api/v1/api-keys/{key_id}")

    async def revoke(self, key_id: str) -> None:
        """Revoke an API key (alias for delete)."""
        await self.delete(key_id)
