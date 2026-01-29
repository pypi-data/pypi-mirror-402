"""Exception hierarchy for the Pylon SDK.

This module provides a comprehensive set of exceptions for different error
scenarios when interacting with the Pylon API. Users can catch specific
exceptions to handle different error cases appropriately.

Example:
    from pylon import PylonClient
    from pylon.exceptions import (
        PylonAuthenticationError,
        PylonNotFoundError,
        PylonRateLimitError,
    )

    client = PylonClient(api_key="...")

    try:
        issue = client.issues.get("nonexistent_id")
    except PylonNotFoundError as e:
        print(f"Issue not found: {e.message}")
    except PylonAuthenticationError:
        print("Invalid API key")
    except PylonRateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after} seconds")
"""

from __future__ import annotations


class PylonError(Exception):
    """Base exception for all Pylon SDK errors.

    All exceptions raised by the Pylon SDK inherit from this class,
    making it easy to catch all SDK-related errors.
    """


class PylonAPIError(PylonError):
    """Base exception for API-related errors.

    This exception is raised when the Pylon API returns an error response.
    It includes the HTTP status code, error message, and optional request ID
    for debugging.

    Attributes:
        status_code: HTTP status code from the API response.
        message: Error message from the API.
        request_id: Request ID for debugging (if available).
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        request_id: str | None = None,
    ) -> None:
        """Initialize a PylonAPIError.

        Args:
            status_code: HTTP status code from the API response.
            message: Error message from the API.
            request_id: Optional request ID for debugging.
        """
        self.status_code = status_code
        self.message = message
        self.request_id = request_id
        super().__init__(f"[{status_code}] {message}")


class PylonAuthenticationError(PylonAPIError):
    """Raised when authentication fails (HTTP 401).

    This typically indicates an invalid or expired API key.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        request_id: str | None = None,
    ) -> None:
        """Initialize a PylonAuthenticationError.

        Args:
            message: Error message (defaults to "Authentication failed").
            request_id: Optional request ID for debugging.
        """
        super().__init__(401, message, request_id)


class PylonRateLimitError(PylonAPIError):
    """Raised when rate limit is exceeded (HTTP 429).

    This exception includes a `retry_after` attribute indicating how many
    seconds to wait before retrying the request.

    Attributes:
        retry_after: Seconds to wait before retrying (if provided by the API).
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        request_id: str | None = None,
    ) -> None:
        """Initialize a PylonRateLimitError.

        Args:
            message: Error message (defaults to "Rate limit exceeded").
            retry_after: Seconds to wait before retrying.
            request_id: Optional request ID for debugging.
        """
        self.retry_after = retry_after
        super().__init__(429, message, request_id)


class PylonNotFoundError(PylonAPIError):
    """Raised when a resource is not found (HTTP 404).

    This typically indicates that the requested resource does not exist
    or the user does not have permission to access it.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        request_id: str | None = None,
    ) -> None:
        """Initialize a PylonNotFoundError.

        Args:
            message: Error message (defaults to "Resource not found").
            request_id: Optional request ID for debugging.
        """
        super().__init__(404, message, request_id)


class PylonValidationError(PylonAPIError):
    """Raised when request validation fails (HTTP 400).

    This exception includes a list of validation errors returned by the API.

    Attributes:
        errors: List of validation error details (if provided by the API).
    """

    def __init__(
        self,
        message: str = "Validation error",
        errors: list[dict[str, str]] | None = None,
        request_id: str | None = None,
    ) -> None:
        """Initialize a PylonValidationError.

        Args:
            message: Error message (defaults to "Validation error").
            errors: List of validation error details.
            request_id: Optional request ID for debugging.
        """
        self.errors = errors or []
        super().__init__(400, message, request_id)


class PylonServerError(PylonAPIError):
    """Raised when the server returns an error (HTTP 5xx).

    This indicates a server-side error that is likely temporary. The request
    should be retried after a short delay.
    """

    def __init__(
        self,
        status_code: int = 500,
        message: str = "Server error",
        request_id: str | None = None,
    ) -> None:
        """Initialize a PylonServerError.

        Args:
            status_code: HTTP status code (defaults to 500).
            message: Error message (defaults to "Server error").
            request_id: Optional request ID for debugging.
        """
        super().__init__(status_code, message, request_id)


class PylonWebhookError(PylonError):
    """Base exception for webhook-related errors.

    This exception is raised when there's an issue processing a webhook.
    """

    def __init__(self, message: str) -> None:
        """Initialize a PylonWebhookError.

        Args:
            message: Description of the webhook error.
        """
        self.message = message
        super().__init__(message)


class PylonWebhookSignatureError(PylonWebhookError):
    """Raised when webhook signature verification fails.

    This indicates that the webhook payload signature does not match
    the expected signature, which could indicate tampering or an
    incorrect webhook secret.
    """

    def __init__(
        self,
        message: str = "Webhook signature verification failed",
    ) -> None:
        """Initialize a PylonWebhookSignatureError.

        Args:
            message: Error message describing the signature failure.
        """
        super().__init__(message)


class PylonWebhookTimestampError(PylonWebhookError):
    """Raised when webhook timestamp validation fails.

    This indicates that the webhook timestamp is outside the acceptable
    time window, which could indicate a replay attack or significant
    clock skew.

    Attributes:
        timestamp: The timestamp from the webhook (if available).
        tolerance_seconds: The maximum allowed time difference.
    """

    def __init__(
        self,
        message: str = "Webhook timestamp validation failed",
        timestamp: str | None = None,
        tolerance_seconds: int | None = None,
    ) -> None:
        """Initialize a PylonWebhookTimestampError.

        Args:
            message: Error message describing the timestamp failure.
            timestamp: The timestamp from the webhook header.
            tolerance_seconds: The allowed tolerance in seconds.
        """
        self.timestamp = timestamp
        self.tolerance_seconds = tolerance_seconds
        super().__init__(message)
