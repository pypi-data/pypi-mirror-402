"""HTTP transport layer for the Pylon SDK.

This module provides the core HTTP functionality using httpx for both
synchronous and asynchronous operations.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import httpx
from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pylon.exceptions import (
    PylonAPIError,
    PylonAuthenticationError,
    PylonNotFoundError,
    PylonRateLimitError,
    PylonServerError,
    PylonValidationError,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

# Default configuration
DEFAULT_BASE_URL = "https://api.usepylon.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


class BaseHTTPTransport(ABC):
    """Abstract base class for HTTP transport.

    Defines the interface for making HTTP requests to the Pylon API.
    Both sync and async implementations inherit from this class.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """Initialize the transport.

        Args:
            api_key: Pylon API key for authentication.
            base_url: Base URL for the Pylon API.
            timeout: Timeout in seconds for HTTP requests.
            max_retries: Maximum number of retry attempts.
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def _build_headers(self) -> dict[str, str]:
        """Build headers for API requests.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _build_url(self, endpoint: str) -> str:
        """Build the full URL for an endpoint.

        Args:
            endpoint: API endpoint path.

        Returns:
            Full URL string.
        """
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/{endpoint}"

    def _handle_response_errors(
        self,
        response: httpx.Response,
    ) -> None:
        """Handle HTTP error responses.

        Args:
            response: The HTTP response.

        Raises:
            PylonAuthenticationError: If authentication fails (401).
            PylonNotFoundError: If resource not found (404).
            PylonRateLimitError: If rate limited (429).
            PylonValidationError: If validation fails (400).
            PylonServerError: If server error (5xx).
            PylonAPIError: For other HTTP errors.
        """
        if response.is_success:
            return

        status_code = response.status_code
        request_id = response.headers.get("x-request-id")

        try:
            error_data = response.json()
            message = error_data.get("message", response.text)
        except Exception:
            message = response.text or f"HTTP {status_code}"

        if status_code == 401:
            raise PylonAuthenticationError(message=message, request_id=request_id)
        elif status_code == 404:
            raise PylonNotFoundError(message=message, request_id=request_id)
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after else None
            raise PylonRateLimitError(
                message=message, retry_after=retry_seconds, request_id=request_id
            )
        elif status_code in (400, 422):
            errors = error_data.get("errors") if "error_data" in dir() else None
            raise PylonValidationError(
                message=message, errors=errors, request_id=request_id
            )
        elif status_code >= 500:
            raise PylonServerError(
                status_code=status_code, message=message, request_id=request_id
            )
        else:
            raise PylonAPIError(
                status_code=status_code, message=message, request_id=request_id
            )

    def _should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry.

        Args:
            exception: The exception to check.

        Returns:
            True if the request should be retried, False otherwise.
        """
        # Retry on rate limit errors (429) and server errors (5xx)
        return isinstance(exception, (PylonRateLimitError, PylonServerError))

    def _wait_for_retry_after(self, exception: Exception) -> None:
        """Wait for the duration specified in Retry-After header if present.

        Args:
            exception: The exception that may contain retry_after information.
        """
        if isinstance(exception, PylonRateLimitError) and exception.retry_after:
            time.sleep(exception.retry_after)

    async def _async_wait_for_retry_after(self, exception: Exception) -> None:
        """Async wait for the duration specified in Retry-After header if present.

        Args:
            exception: The exception that may contain retry_after information.
        """
        if isinstance(exception, PylonRateLimitError) and exception.retry_after:
            await asyncio.sleep(exception.retry_after)

    @abstractmethod
    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            endpoint: API endpoint path.
            params: Query parameters.
            json: JSON body data.

        Returns:
            Parsed JSON response.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the transport and release resources."""
        ...


class SyncHTTPTransport(BaseHTTPTransport):
    """Synchronous HTTP transport using httpx.Client.

    Provides connection pooling and HTTP/2 support for efficient
    synchronous API calls.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """Initialize the synchronous transport.

        Args:
            api_key: Pylon API key for authentication.
            base_url: Base URL for the Pylon API.
            timeout: Timeout in seconds for HTTP requests.
            max_retries: Maximum number of retry attempts.
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._client = httpx.Client(
            headers=self._build_headers(),
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a synchronous HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            endpoint: API endpoint path.
            params: Query parameters.
            json: JSON body data.

        Returns:
            Parsed JSON response.

        Raises:
            PylonAPIError: If the request fails after all retries.
        """
        url = self._build_url(endpoint)
        last_exception: Exception | None = None

        # Use tenacity for retry logic
        for attempt in Retrying(
            retry=retry_if_exception_type((PylonRateLimitError, PylonServerError)),
            stop=stop_after_attempt(self.max_retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=60),
            reraise=True,
        ):
            with attempt:
                try:
                    response = self._client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json,
                    )
                    self._handle_response_errors(response)
                    result: dict[str, Any] = response.json()
                    return result
                except (PylonRateLimitError, PylonServerError) as e:
                    # Wait for Retry-After header if present
                    self._wait_for_retry_after(e)
                    last_exception = e
                    raise

        # This should never be reached due to reraise=True, but satisfies mypy
        if last_exception:
            raise last_exception
        raise PylonAPIError(status_code=500, message="Request failed")

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> SyncHTTPTransport:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit."""
        self.close()


class AsyncHTTPTransport(BaseHTTPTransport):
    """Asynchronous HTTP transport using httpx.AsyncClient.

    Provides connection pooling and HTTP/2 support for efficient
    asynchronous API calls.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """Initialize the asynchronous transport.

        Args:
            api_key: Pylon API key for authentication.
            base_url: Base URL for the Pylon API.
            timeout: Timeout in seconds for HTTP requests.
            max_retries: Maximum number of retry attempts.
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._client = httpx.AsyncClient(
            headers=self._build_headers(),
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Synchronous request is not supported for async transport.

        Use arequest() instead.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError(
            "Use arequest() for async transport. "
            "This method exists only for interface compatibility."
        )

    async def arequest(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an asynchronous HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            endpoint: API endpoint path.
            params: Query parameters.
            json: JSON body data.

        Returns:
            Parsed JSON response.

        Raises:
            PylonAPIError: If the request fails after all retries.
        """
        url = self._build_url(endpoint)
        last_exception: Exception | None = None

        # Use tenacity for async retry logic
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type((PylonRateLimitError, PylonServerError)),
            stop=stop_after_attempt(self.max_retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=60),
            reraise=True,
        ):
            with attempt:
                try:
                    response = await self._client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json,
                    )
                    self._handle_response_errors(response)
                    result: dict[str, Any] = response.json()
                    return result
                except (PylonRateLimitError, PylonServerError) as e:
                    # Wait for Retry-After header if present
                    await self._async_wait_for_retry_after(e)
                    last_exception = e
                    raise

        # This should never be reached due to reraise=True, but satisfies mypy
        if last_exception:
            raise last_exception
        raise PylonAPIError(status_code=500, message="Request failed")

    def close(self) -> None:
        """Synchronous close is not supported for async transport.

        Use aclose() instead.
        """
        raise NotImplementedError(
            "Use aclose() for async transport. "
            "This method exists only for interface compatibility."
        )

    async def aclose(self) -> None:
        """Close the async HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHTTPTransport:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.aclose()
