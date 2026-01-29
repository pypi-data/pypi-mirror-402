"""HTTP client wrapper for SEE URL SDK."""

import asyncio
from typing import Any, cast
from urllib.parse import urljoin

import httpx

from .exceptions import (
    APIError,
)
from .version import __version__


class HttpClient:
    """Async HTTP client for API requests."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://s.ee/api",
        timeout: float = 30.0,
        max_retries: int = 3,
        proxy: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.proxy = proxy
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "HttpClient":
        """Async context manager entry."""
        client_kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            "headers": {
                "Authorization": self.api_key,
                "User-Agent": f"see-python-sdk/{__version__}",
            },
        }
        if self.proxy:
            client_kwargs["proxy"] = self.proxy

        self._client = httpx.AsyncClient(**client_kwargs)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_url(self, path: str) -> str:
        """Construct full URL from path."""
        return urljoin(f"{self.base_url}/", path.lstrip("/"))

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and raise appropriate exceptions."""
        try:
            data = response.json()
        except Exception:
            data = {"content": response.text}

        if response.status_code in (200, 201):
            return data

        raise APIError(
            message=f"API request failed: {response.status_code}",
            status_code=response.status_code,
            response_data=data,
        )

    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        """Make an HTTP request with retry logic."""
        if not self._client:
            raise RuntimeError("HttpClient must be used as async context manager")

        # Set default Content-Type to application/json if not present and not uploading files
        if "files" not in kwargs:
            headers = kwargs.get("headers", {})
            if "Content-Type" not in headers:
                if "headers" not in kwargs:
                    kwargs["headers"] = {}
                kwargs["headers"]["Content-Type"] = "application/json"

        url = self._get_url(path)
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(method, url, **kwargs)
                return self._handle_response(response)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                continue
            except APIError:
                raise
            except httpx.HTTPError as e:
                raise APIError(f"HTTP error occurred: {e}") from e

        raise APIError(
            f"Request failed after {self.max_retries} attempts: {last_exception}"
        ) from last_exception

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make a GET request."""
        return cast(dict[str, Any], await self.request("GET", path, **kwargs))

    async def post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make a POST request."""
        return cast(dict[str, Any], await self.request("POST", path, **kwargs))

    async def put(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make a PUT request."""
        return cast(dict[str, Any], await self.request("PUT", path, **kwargs))

    async def delete(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make a DELETE request."""
        return cast(dict[str, Any], await self.request("DELETE", path, **kwargs))
