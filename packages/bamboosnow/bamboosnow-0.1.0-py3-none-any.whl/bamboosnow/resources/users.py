"""
Users Resource

Resource for user account operations.
"""

from __future__ import annotations

from bamboosnow.http import AsyncHttpClient, HttpClient
from bamboosnow.types import User


class UsersResource:
    """
    Resource for user account operations.

    Example:
        >>> # Get current user
        >>> user = client.users.me()
        >>> print(user.email)
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def me(self) -> User:
        """
        Get the current authenticated user.

        Returns:
            The current user's profile
        """
        data = self._http.get("/api/v1/users/me")
        return User.model_validate(data)

    def get(self, user_id: str) -> User:
        """
        Get a user by ID.

        Args:
            user_id: The user ID

        Returns:
            The user profile
        """
        data = self._http.get(f"/api/v1/users/{user_id}")
        return User.model_validate(data)


class AsyncUsersResource:
    """Async resource for user account operations."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def me(self) -> User:
        """Get the current authenticated user."""
        data = await self._http.get("/api/v1/users/me")
        return User.model_validate(data)

    async def get(self, user_id: str) -> User:
        """Get a user by ID."""
        data = await self._http.get(f"/api/v1/users/{user_id}")
        return User.model_validate(data)
