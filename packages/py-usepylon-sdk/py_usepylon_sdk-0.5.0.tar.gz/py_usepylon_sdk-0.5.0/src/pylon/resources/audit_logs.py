"""Audit logs resource for the Pylon SDK.

This module provides resource classes for interacting with the
Pylon Audit Logs API endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pylon.models.audit_logs import PylonAuditLog
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


def _format_datetime_utc(dt: datetime) -> str:
    """Format datetime as UTC ISO 8601 string.

    Converts timezone-aware datetimes to UTC before formatting.
    Naive datetimes are assumed to already be in UTC.

    Args:
        dt: The datetime to format.

    Returns:
        ISO 8601 formatted string with Z suffix (UTC).
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class AuditLogsResource(BaseSyncResource[PylonAuditLog]):
    """Synchronous resource for accessing Pylon audit logs.

    Provides methods for listing and searching audit log entries.
    Audit logs are read-only.
    """

    _endpoint = "/audit_logs"
    _model = PylonAuditLog

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the audit logs resource."""
        super().__init__(transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonAuditLog]:
        """List audit log entries.

        Args:
            limit: Number of items per page.

        Yields:
            PylonAuditLog instances.
        """
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonAuditLog.from_pylon_dict,
        )
        yield from paginator.iter()

    def search(
        self,
        *,
        action: str | None = None,
        resource_type: str | None = None,
        actor_id: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = 100,
        **kwargs: Any,
    ) -> Iterator[PylonAuditLog]:
        """Search audit logs with filters.

        Args:
            action: Filter by action type.
            resource_type: Filter by resource type.
            actor_id: Filter by actor user ID.
            created_after: Filter logs created after this datetime.
            created_before: Filter logs created before this datetime.
            limit: Maximum number of results.
            **kwargs: Additional filter parameters.

        Yields:
            Matching PylonAuditLog instances.
        """
        params: dict[str, Any] = {"limit": limit, **kwargs}
        if action:
            params["action"] = action
        if resource_type:
            params["resource_type"] = resource_type
        if actor_id:
            params["actor_id"] = actor_id
        if created_after:
            params["created_after"] = _format_datetime_utc(created_after)
        if created_before:
            params["created_before"] = _format_datetime_utc(created_before)

        response = self._get(f"{self._endpoint}/search", params=params)
        items = response.get("data", [])
        for item in items:
            yield PylonAuditLog.from_pylon_dict(item)

        # Handle pagination
        while response.get("pagination", {}).get("has_next_page"):
            cursor = response["pagination"]["cursor"]
            params["cursor"] = cursor
            response = self._get(f"{self._endpoint}/search", params=params)
            items = response.get("data", [])
            for item in items:
                yield PylonAuditLog.from_pylon_dict(item)


class AsyncAuditLogsResource(BaseAsyncResource[PylonAuditLog]):
    """Asynchronous resource for accessing Pylon audit logs.

    Provides async methods for listing and searching audit log entries.
    Audit logs are read-only.
    """

    _endpoint = "/audit_logs"
    _model = PylonAuditLog

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the async audit logs resource."""
        super().__init__(transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonAuditLog]:
        """List audit log entries asynchronously.

        Args:
            limit: Number of items per page.

        Yields:
            PylonAuditLog instances.
        """
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonAuditLog.from_pylon_dict,
        )
        async for log in paginator:
            yield log

    async def search(
        self,
        *,
        action: str | None = None,
        resource_type: str | None = None,
        actor_id: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = 100,
        **kwargs: Any,
    ) -> AsyncIterator[PylonAuditLog]:
        """Search audit logs with filters asynchronously.

        Args:
            action: Filter by action type.
            resource_type: Filter by resource type.
            actor_id: Filter by actor user ID.
            created_after: Filter logs created after this datetime.
            created_before: Filter logs created before this datetime.
            limit: Maximum number of results.
            **kwargs: Additional filter parameters.

        Yields:
            Matching PylonAuditLog instances.
        """
        params: dict[str, Any] = {"limit": limit, **kwargs}
        if action:
            params["action"] = action
        if resource_type:
            params["resource_type"] = resource_type
        if actor_id:
            params["actor_id"] = actor_id
        if created_after:
            params["created_after"] = _format_datetime_utc(created_after)
        if created_before:
            params["created_before"] = _format_datetime_utc(created_before)

        response = await self._get(f"{self._endpoint}/search", params=params)
        items = response.get("data", [])
        for item in items:
            yield PylonAuditLog.from_pylon_dict(item)

        # Handle pagination
        while response.get("pagination", {}).get("has_next_page"):
            cursor = response["pagination"]["cursor"]
            params["cursor"] = cursor
            response = await self._get(f"{self._endpoint}/search", params=params)
            items = response.get("data", [])
            for item in items:
                yield PylonAuditLog.from_pylon_dict(item)
