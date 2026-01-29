"""
BambooSnow SDK HTTP Client

Low-level HTTP client for making API requests.
"""

from __future__ import annotations

import time
from typing import Any, TypeVar

import httpx

from bamboosnow.errors import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

T = TypeVar("T")

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class HttpClient:
    """HTTP client for BambooSnow API requests."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._build_headers(),
        )

    def _build_headers(self) -> dict[str, str]:
        """Build default headers for requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "bamboosnow-python/0.1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle error responses and raise appropriate exceptions."""
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text}

        message = body.get("message", body.get("error", f"HTTP {response.status_code}"))

        if response.status_code == 401:
            raise AuthenticationError(message, response_body=body)
        elif response.status_code == 404:
            raise NotFoundError(message, response_body=body)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                response_body=body,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif response.status_code in (400, 422):
            raise ValidationError(
                message,
                status_code=response.status_code,
                response_body=body,
                errors=body.get("errors"),
            )
        else:
            raise APIError(message, status_code=response.status_code, response_body=body)

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | str | None:
        """Make an HTTP request with retry logic."""
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = self._client.request(
                    method=method,
                    url=path,
                    json=json,
                    params=params,
                )

                if response.status_code >= 400:
                    if response.status_code in RETRY_STATUS_CODES and attempt < self.max_retries - 1:
                        wait_time = 2**attempt
                        if response.status_code == 429:
                            retry_after = response.headers.get("Retry-After")
                            if retry_after:
                                wait_time = int(retry_after)
                        time.sleep(wait_time)
                        continue
                    self._handle_error(response)

                if response.status_code == 204:
                    return None

                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    return response.json()
                return response.text

            except httpx.RequestError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise APIError(f"Request failed: {e}") from e

        if last_error:
            raise APIError(f"Request failed after {self.max_retries} retries: {last_error}")
        raise APIError("Request failed")

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request."""
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make a POST request."""
        return self._request("POST", path, json=json)

    def patch(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make a PATCH request."""
        return self._request("PATCH", path, json=json)

    def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make a PUT request."""
        return self._request("PUT", path, json=json)

    def delete(self, path: str) -> Any:
        """Make a DELETE request."""
        return self._request("DELETE", path)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncHttpClient:
    """Async HTTP client for BambooSnow API requests."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._build_headers(),
        )

    def _build_headers(self) -> dict[str, str]:
        """Build default headers for requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "bamboosnow-python/0.1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle error responses and raise appropriate exceptions."""
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text}

        message = body.get("message", body.get("error", f"HTTP {response.status_code}"))

        if response.status_code == 401:
            raise AuthenticationError(message, response_body=body)
        elif response.status_code == 404:
            raise NotFoundError(message, response_body=body)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                response_body=body,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif response.status_code in (400, 422):
            raise ValidationError(
                message,
                status_code=response.status_code,
                response_body=body,
                errors=body.get("errors"),
            )
        else:
            raise APIError(message, status_code=response.status_code, response_body=body)

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | str | None:
        """Make an HTTP request with retry logic."""
        import asyncio

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(
                    method=method,
                    url=path,
                    json=json,
                    params=params,
                )

                if response.status_code >= 400:
                    if response.status_code in RETRY_STATUS_CODES and attempt < self.max_retries - 1:
                        wait_time = 2**attempt
                        if response.status_code == 429:
                            retry_after = response.headers.get("Retry-After")
                            if retry_after:
                                wait_time = int(retry_after)
                        await asyncio.sleep(wait_time)
                        continue
                    self._handle_error(response)

                if response.status_code == 204:
                    return None

                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    return response.json()
                return response.text

            except httpx.RequestError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                raise APIError(f"Request failed: {e}") from e

        if last_error:
            raise APIError(f"Request failed after {self.max_retries} retries: {last_error}")
        raise APIError("Request failed")

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request."""
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make a POST request."""
        return await self._request("POST", path, json=json)

    async def patch(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make a PATCH request."""
        return await self._request("PATCH", path, json=json)

    async def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make a PUT request."""
        return await self._request("PUT", path, json=json)

    async def delete(self, path: str) -> Any:
        """Make a DELETE request."""
        return await self._request("DELETE", path)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
