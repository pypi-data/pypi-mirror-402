"""Issues resource for the Pylon SDK.

This module provides resource classes for interacting with the
Pylon Issues API endpoint.
"""

from __future__ import annotations

import builtins
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pylon.models import PylonIssue, PylonMessage
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._client import AsyncPylonClient, PylonClient
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


class IssuesResource(BaseSyncResource[PylonIssue]):
    """Synchronous resource for managing Pylon issues.

    Provides methods for listing, retrieving, creating, and updating
    issues via the Pylon API.

    Example:
        client = PylonClient(api_key="...")

        # List recent issues
        for issue in client.issues.list(days=7):
            print(f"#{issue.number}: {issue.title}")

        # Get a specific issue
        issue = client.issues.get("issue_123")

        # Rich methods (available on returned issues)
        issue.resolve()
        issue.add_message("Thanks for your feedback!")
    """

    _endpoint = "/issues"
    _model = PylonIssue

    def __init__(
        self,
        transport: SyncHTTPTransport,
        client: PylonClient | None = None,
    ) -> None:
        """Initialize the issues resource.

        Args:
            transport: The HTTP transport to use for requests.
            client: Optional client reference for rich model methods.
        """
        super().__init__(transport)
        self._client = client

    def _inject_transport(self, issue: PylonIssue) -> PylonIssue:
        """Inject transport and client into issue for rich methods."""
        issue._with_sync_transport(self._transport)
        if self._client:
            issue._bind_client(self._client)
        return issue

    def list(
        self,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        days: int | None = None,
        limit: int = 100,
    ) -> Iterator[PylonIssue]:
        """List issues with optional time filtering.

        Args:
            start_time: Start of time range filter.
            end_time: End of time range filter.
            days: Number of days to look back (alternative to start_time).
            limit: Number of items per page.

        Yields:
            PylonIssue instances.
        """
        # Calculate time range
        if end_time is None:
            end_time = datetime.now(UTC)

        if start_time is None and days is not None:
            from datetime import timedelta

            start_time = end_time - timedelta(days=days)

        params: dict[str, Any] = {"limit": limit}
        if start_time:
            params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if end_time:
            params["end_time"] = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params=params,
            parser=PylonIssue.from_pylon_dict,
        )
        for issue in paginator.iter():
            yield self._inject_transport(issue)

    def get(self, issue_id: str) -> PylonIssue:
        """Get a specific issue by ID.

        Args:
            issue_id: The issue ID or ticket number.

        Returns:
            The PylonIssue instance with transport for sub-resource access.
        """
        response = self._get(f"{self._endpoint}/{issue_id}")
        data = response.get("data", response)
        issue = PylonIssue.from_pylon_dict(data)
        return self._inject_transport(issue)

    def get_by_number(self, number: int) -> PylonIssue | None:
        """Get an issue by its ticket number.

        Args:
            number: The human-readable ticket number.

        Returns:
            The PylonIssue instance or None if not found.
        """
        from pylon.exceptions import PylonNotFoundError

        try:
            return self.get(str(number))
        except PylonNotFoundError:
            return None

    def update(self, issue_id: str, **kwargs: Any) -> PylonIssue:
        """Update an issue.

        Args:
            issue_id: The issue ID to update.
            **kwargs: Fields to update.

        Returns:
            The updated PylonIssue instance with transport for sub-resource access.
        """
        response = self._patch(f"{self._endpoint}/{issue_id}", data=kwargs)
        data = response.get("data", response)
        issue = PylonIssue.from_pylon_dict(data)
        return self._inject_transport(issue)

    def create(
        self,
        *,
        title: str,
        description: str,
        status: str = "open",
        priority: str = "medium",
        assignee: str | None = None,
        **kwargs: Any,
    ) -> PylonIssue:
        """Create a new issue.

        Args:
            title: Issue title.
            description: Issue description.
            status: Issue status (default: "open").
            priority: Issue priority (default: "medium").
            assignee: Optional assignee user ID or email.
            **kwargs: Additional fields.

        Returns:
            The created PylonIssue instance with transport for sub-resource access.
        """
        data = {
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            **kwargs,
        }
        if assignee:
            data["assignee"] = assignee
        response = self._post(self._endpoint, data=data)
        result = response.get("data", response)
        issue = PylonIssue.from_pylon_dict(result)
        return self._inject_transport(issue)

    def search(
        self,
        query: str = "",
        *,
        state: str | None = None,
        priority: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        assigned_to: str | None = None,
        tags: builtins.list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> Iterator[PylonIssue]:
        """Search for issues with typed filter parameters.

        Args:
            query: Search query string.
            state: Filter by issue state (e.g., "open", "resolved", "closed").
            priority: Filter by priority (e.g., "low", "medium", "high", "urgent").
            created_after: Filter issues created after this datetime.
            created_before: Filter issues created before this datetime.
            assigned_to: Filter by assignee user ID or email.
            tags: Filter by list of tag IDs.
            filters: Additional filters as key-value pairs (legacy).
            limit: Maximum number of results.

        Yields:
            Matching PylonIssue instances with transport for sub-resource access.
        """
        payload: dict[str, Any] = {"limit": limit}
        if query:
            payload["query"] = query

        # Build filters from typed parameters
        filter_list: builtins.list[dict[str, Any]] = []
        if state:
            filter_list.append({"field": "state", "operator": "equals", "value": state})
        if priority:
            filter_list.append(
                {"field": "priority", "operator": "equals", "value": priority}
            )
        if created_after:
            filter_list.append(
                {
                    "field": "created_at",
                    "operator": "gte",
                    "value": _format_datetime_utc(created_after),
                }
            )
        if created_before:
            filter_list.append(
                {
                    "field": "created_at",
                    "operator": "lte",
                    "value": _format_datetime_utc(created_before),
                }
            )
        if assigned_to:
            filter_list.append(
                {"field": "assignee", "operator": "equals", "value": assigned_to}
            )
        if tags:
            filter_list.append({"field": "tags", "operator": "in", "value": tags})

        if filter_list:
            payload["filters"] = filter_list
        elif filters:
            payload["filters"] = filters

        response = self._post(f"{self._endpoint}/search", data=payload)
        items = response.get("data", [])
        for item in items:
            yield self._inject_transport(PylonIssue.from_pylon_dict(item))

        # Handle pagination
        while response.get("pagination", {}).get("has_next_page"):
            cursor = response["pagination"]["cursor"]
            payload["cursor"] = cursor
            response = self._post(f"{self._endpoint}/search", data=payload)
            items = response.get("data", [])
            for item in items:
                yield self._inject_transport(PylonIssue.from_pylon_dict(item))

    def snooze(self, issue_id: str, *, until: datetime | str) -> PylonIssue:
        """Snooze an issue until a specific date/time.

        Args:
            issue_id: The issue ID to snooze.
            until: Date/time when issue should reappear (ISO 8601 or datetime).

        Returns:
            The updated PylonIssue instance with transport for sub-resource access.
        """
        if isinstance(until, datetime):
            # Normalize to UTC before formatting (naive datetimes assumed to be UTC)
            until_utc = until.astimezone(UTC) if until.tzinfo is not None else until
            until_str = until_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            until_str = until
        response = self._post(
            f"{self._endpoint}/{issue_id}/snooze", data={"until": until_str}
        )
        data = response.get("data", response)
        issue = PylonIssue.from_pylon_dict(data)
        return self._inject_transport(issue)

    def bulk_update(
        self,
        issue_ids: builtins.list[str],
        **updates: Any,
    ) -> builtins.list[PylonIssue]:
        """Update multiple issues at once.

        Args:
            issue_ids: List of issue IDs to update.
            **updates: Fields to update on all issues.

        Returns:
            List of updated PylonIssue instances.
        """
        payload = {"issue_ids": issue_ids, "updates": updates}
        response = self._post(f"{self._endpoint}/bulk/update", data=payload)
        items = response.get("data", [])
        return [
            self._inject_transport(PylonIssue.from_pylon_dict(item)) for item in items
        ]

    def bulk_assign(
        self,
        issue_ids: builtins.list[str],
        assignee: str,
    ) -> builtins.list[PylonIssue]:
        """Assign multiple issues to a user.

        Args:
            issue_ids: List of issue IDs to assign.
            assignee: User ID or email to assign issues to.

        Returns:
            List of updated PylonIssue instances.
        """
        return self.bulk_update(issue_ids, assignee=assignee)

    def bulk_add_tags(
        self,
        issue_ids: builtins.list[str],
        tags: builtins.list[str],
    ) -> builtins.list[PylonIssue]:
        """Add tags to multiple issues.

        Args:
            issue_ids: List of issue IDs.
            tags: List of tag IDs to add.

        Returns:
            List of updated PylonIssue instances.
        """
        payload = {"issue_ids": issue_ids, "tags": tags}
        response = self._post(f"{self._endpoint}/bulk/add_tags", data=payload)
        items = response.get("data", [])
        return [
            self._inject_transport(PylonIssue.from_pylon_dict(item)) for item in items
        ]

    def bulk_remove_tags(
        self,
        issue_ids: builtins.list[str],
        tags: builtins.list[str],
    ) -> builtins.list[PylonIssue]:
        """Remove tags from multiple issues.

        Args:
            issue_ids: List of issue IDs.
            tags: List of tag IDs to remove.

        Returns:
            List of updated PylonIssue instances.
        """
        payload = {"issue_ids": issue_ids, "tags": tags}
        response = self._post(f"{self._endpoint}/bulk/remove_tags", data=payload)
        items = response.get("data", [])
        return [
            self._inject_transport(PylonIssue.from_pylon_dict(item)) for item in items
        ]

    def messages(
        self, issue_id: str, limit: int | None = None
    ) -> builtins.list[PylonMessage]:
        """Get messages for a specific issue.

        Args:
            issue_id: The issue ID.
            limit: Maximum number of messages to retrieve.

        Returns:
            List of PylonMessage instances.
        """
        params: dict[str, Any] = {}
        if limit:
            params["limit"] = limit

        response = self._get(f"{self._endpoint}/{issue_id}/messages", params=params)
        items = response.get("data", [])
        return [PylonMessage.from_pylon_dict(item) for item in items]


class AsyncIssuesResource(BaseAsyncResource[PylonIssue]):
    """Asynchronous resource for managing Pylon issues.

    Provides async methods for listing, retrieving, creating, and updating
    issues via the Pylon API.

    Example:
        async with AsyncPylonClient(api_key="...") as client:
            # List recent issues
            async for issue in client.issues.list(days=7):
                print(f"#{issue.number}: {issue.title}")

            # Get a specific issue
            issue = await client.issues.get("issue_123")

            # Rich methods (available on returned issues)
            await issue.resolve()
            await issue.add_message("Thanks for your feedback!")
    """

    _endpoint = "/issues"
    _model = PylonIssue

    def __init__(
        self,
        transport: AsyncHTTPTransport,
        client: AsyncPylonClient | None = None,
    ) -> None:
        """Initialize the async issues resource.

        Args:
            transport: The async HTTP transport to use for requests.
            client: Optional client reference for rich model methods.
        """
        super().__init__(transport)
        self._client = client

    def _inject_transport(self, issue: PylonIssue) -> PylonIssue:
        """Inject transport and client into issue for rich methods."""
        issue._with_async_transport(self._transport)
        if self._client:
            issue._bind_client(self._client)
        return issue

    async def list(
        self,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        days: int | None = None,
        limit: int = 100,
    ) -> AsyncIterator[PylonIssue]:
        """List issues asynchronously with optional time filtering.

        Args:
            start_time: Start of time range filter.
            end_time: End of time range filter.
            days: Number of days to look back (alternative to start_time).
            limit: Number of items per page.

        Yields:
            PylonIssue instances with transport for sub-resource access.
        """
        # Calculate time range
        if end_time is None:
            end_time = datetime.now(UTC)

        if start_time is None and days is not None:
            from datetime import timedelta

            start_time = end_time - timedelta(days=days)

        params: dict[str, Any] = {"limit": limit}
        if start_time:
            params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if end_time:
            params["end_time"] = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params=params,
            parser=PylonIssue.from_pylon_dict,
        )
        async for issue in paginator:
            yield self._inject_transport(issue)

    async def get(self, issue_id: str) -> PylonIssue:
        """Get a specific issue by ID asynchronously.

        Args:
            issue_id: The issue ID or ticket number.

        Returns:
            The PylonIssue instance with transport for sub-resource access.
        """
        response = await self._get(f"{self._endpoint}/{issue_id}")
        data = response.get("data", response)
        issue = PylonIssue.from_pylon_dict(data)
        return self._inject_transport(issue)

    async def get_by_number(self, number: int) -> PylonIssue | None:
        """Get an issue by its ticket number asynchronously.

        Args:
            number: The human-readable ticket number.

        Returns:
            The PylonIssue instance or None if not found.
        """
        from pylon.exceptions import PylonNotFoundError

        try:
            return await self.get(str(number))
        except PylonNotFoundError:
            return None

    async def update(self, issue_id: str, **kwargs: Any) -> PylonIssue:
        """Update an issue asynchronously.

        Args:
            issue_id: The issue ID to update.
            **kwargs: Fields to update.

        Returns:
            The updated PylonIssue instance with transport for sub-resource access.
        """
        response = await self._patch(f"{self._endpoint}/{issue_id}", data=kwargs)
        data = response.get("data", response)
        issue = PylonIssue.from_pylon_dict(data)
        return self._inject_transport(issue)

    async def create(
        self,
        *,
        title: str,
        description: str,
        status: str = "open",
        priority: str = "medium",
        assignee: str | None = None,
        **kwargs: Any,
    ) -> PylonIssue:
        """Create a new issue asynchronously.

        Args:
            title: Issue title.
            description: Issue description.
            status: Issue status (default: "open").
            priority: Issue priority (default: "medium").
            assignee: Optional assignee user ID or email.
            **kwargs: Additional fields.

        Returns:
            The created PylonIssue instance with transport for sub-resource access.
        """
        data = {
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            **kwargs,
        }
        if assignee:
            data["assignee"] = assignee
        response = await self._post(self._endpoint, data=data)
        result = response.get("data", response)
        issue = PylonIssue.from_pylon_dict(result)
        return self._inject_transport(issue)

    async def search(
        self,
        query: str = "",
        *,
        state: str | None = None,
        priority: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        assigned_to: str | None = None,
        tags: builtins.list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> AsyncIterator[PylonIssue]:
        """Search for issues asynchronously with typed filter parameters.

        Args:
            query: Search query string.
            state: Filter by issue state (e.g., "open", "resolved", "closed").
            priority: Filter by priority (e.g., "low", "medium", "high", "urgent").
            created_after: Filter issues created after this datetime.
            created_before: Filter issues created before this datetime.
            assigned_to: Filter by assignee user ID or email.
            tags: Filter by list of tag IDs.
            filters: Additional filters as key-value pairs (legacy).
            limit: Maximum number of results.

        Yields:
            Matching PylonIssue instances with transport for sub-resource access.
        """
        payload: dict[str, Any] = {"limit": limit}
        if query:
            payload["query"] = query

        # Build filters from typed parameters
        filter_list: builtins.list[dict[str, Any]] = []
        if state:
            filter_list.append({"field": "state", "operator": "equals", "value": state})
        if priority:
            filter_list.append(
                {"field": "priority", "operator": "equals", "value": priority}
            )
        if created_after:
            filter_list.append(
                {
                    "field": "created_at",
                    "operator": "gte",
                    "value": _format_datetime_utc(created_after),
                }
            )
        if created_before:
            filter_list.append(
                {
                    "field": "created_at",
                    "operator": "lte",
                    "value": _format_datetime_utc(created_before),
                }
            )
        if assigned_to:
            filter_list.append(
                {"field": "assignee", "operator": "equals", "value": assigned_to}
            )
        if tags:
            filter_list.append({"field": "tags", "operator": "in", "value": tags})

        if filter_list:
            payload["filters"] = filter_list
        elif filters:
            payload["filters"] = filters

        response = await self._post(f"{self._endpoint}/search", data=payload)
        items = response.get("data", [])
        for item in items:
            yield self._inject_transport(PylonIssue.from_pylon_dict(item))

        # Handle pagination
        while response.get("pagination", {}).get("has_next_page"):
            cursor = response["pagination"]["cursor"]
            payload["cursor"] = cursor
            response = await self._post(f"{self._endpoint}/search", data=payload)
            items = response.get("data", [])
            for item in items:
                yield self._inject_transport(PylonIssue.from_pylon_dict(item))

    async def snooze(self, issue_id: str, *, until: datetime | str) -> PylonIssue:
        """Snooze an issue until a specific date/time asynchronously.

        Args:
            issue_id: The issue ID to snooze.
            until: Date/time when issue should reappear (ISO 8601 or datetime).

        Returns:
            The updated PylonIssue instance with transport for sub-resource access.
        """
        if isinstance(until, datetime):
            # Normalize to UTC before formatting (naive datetimes assumed to be UTC)
            until_utc = until.astimezone(UTC) if until.tzinfo is not None else until
            until_str = until_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            until_str = until
        response = await self._post(
            f"{self._endpoint}/{issue_id}/snooze", data={"until": until_str}
        )
        data = response.get("data", response)
        issue = PylonIssue.from_pylon_dict(data)
        return self._inject_transport(issue)

    async def bulk_update(
        self,
        issue_ids: builtins.list[str],
        **updates: Any,
    ) -> builtins.list[PylonIssue]:
        """Update multiple issues at once asynchronously.

        Args:
            issue_ids: List of issue IDs to update.
            **updates: Fields to update on all issues.

        Returns:
            List of updated PylonIssue instances.
        """
        payload = {"issue_ids": issue_ids, "updates": updates}
        response = await self._post(f"{self._endpoint}/bulk/update", data=payload)
        items = response.get("data", [])
        return [
            self._inject_transport(PylonIssue.from_pylon_dict(item)) for item in items
        ]

    async def bulk_assign(
        self,
        issue_ids: builtins.list[str],
        assignee: str,
    ) -> builtins.list[PylonIssue]:
        """Assign multiple issues to a user asynchronously.

        Args:
            issue_ids: List of issue IDs to assign.
            assignee: User ID or email to assign issues to.

        Returns:
            List of updated PylonIssue instances.
        """
        return await self.bulk_update(issue_ids, assignee=assignee)

    async def bulk_add_tags(
        self,
        issue_ids: builtins.list[str],
        tags: builtins.list[str],
    ) -> builtins.list[PylonIssue]:
        """Add tags to multiple issues asynchronously.

        Args:
            issue_ids: List of issue IDs.
            tags: List of tag IDs to add.

        Returns:
            List of updated PylonIssue instances.
        """
        payload = {"issue_ids": issue_ids, "tags": tags}
        response = await self._post(f"{self._endpoint}/bulk/add_tags", data=payload)
        items = response.get("data", [])
        return [
            self._inject_transport(PylonIssue.from_pylon_dict(item)) for item in items
        ]

    async def bulk_remove_tags(
        self,
        issue_ids: builtins.list[str],
        tags: builtins.list[str],
    ) -> builtins.list[PylonIssue]:
        """Remove tags from multiple issues asynchronously.

        Args:
            issue_ids: List of issue IDs.
            tags: List of tag IDs to remove.

        Returns:
            List of updated PylonIssue instances.
        """
        payload = {"issue_ids": issue_ids, "tags": tags}
        response = await self._post(f"{self._endpoint}/bulk/remove_tags", data=payload)
        items = response.get("data", [])
        return [
            self._inject_transport(PylonIssue.from_pylon_dict(item)) for item in items
        ]

    async def messages(
        self, issue_id: str, limit: int | None = None
    ) -> builtins.list[PylonMessage]:
        """Get messages for a specific issue asynchronously.

        Args:
            issue_id: The issue ID.
            limit: Maximum number of messages to retrieve.

        Returns:
            List of PylonMessage instances.
        """
        params: dict[str, Any] = {}
        if limit:
            params["limit"] = limit

        response = await self._get(
            f"{self._endpoint}/{issue_id}/messages", params=params
        )
        items = response.get("data", [])
        return [PylonMessage.from_pylon_dict(item) for item in items]
