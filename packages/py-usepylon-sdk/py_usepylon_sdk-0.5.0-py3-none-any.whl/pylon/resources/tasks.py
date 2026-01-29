"""Tasks resource for the Pylon SDK.

This module provides resource classes for interacting with the
Pylon Tasks API endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

from pylon.models.tasks import PylonTask
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class TasksResource(BaseSyncResource[PylonTask]):
    """Synchronous resource for managing Pylon tasks.

    Provides methods for listing, retrieving, creating, and updating tasks.
    """

    _endpoint = "/tasks"
    _model = PylonTask

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the tasks resource."""
        super().__init__(transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonTask]:
        """List all tasks.

        Args:
            limit: Number of items per page.

        Yields:
            PylonTask instances.
        """
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonTask.from_pylon_dict,
        )
        yield from paginator.iter()

    def get(self, task_id: str) -> PylonTask:
        """Get a specific task by ID.

        Args:
            task_id: The task ID.

        Returns:
            The PylonTask instance.
        """
        response = self._get(f"{self._endpoint}/{task_id}")
        data = response.get("data", response)
        return PylonTask.from_pylon_dict(data)

    def create(
        self,
        *,
        title: str,
        issue_id: str | None = None,
        assignee_id: str | None = None,
        **kwargs: Any,
    ) -> PylonTask:
        """Create a new task.

        Args:
            title: Task title/description.
            issue_id: ID of the issue to attach the task to.
            assignee_id: ID of the user to assign the task to.
            **kwargs: Additional fields.

        Returns:
            The created PylonTask instance.
        """
        data: dict[str, Any] = {"title": title, **kwargs}
        if issue_id:
            data["issue_id"] = issue_id
        if assignee_id:
            data["assignee_id"] = assignee_id
        response = self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonTask.from_pylon_dict(result)

    def update(self, task_id: str, **kwargs: Any) -> PylonTask:
        """Update an existing task.

        Args:
            task_id: The task ID to update.
            **kwargs: Fields to update.

        Returns:
            The updated PylonTask instance.
        """
        response = self._patch(f"{self._endpoint}/{task_id}", data=kwargs)
        data = response.get("data", response)
        return PylonTask.from_pylon_dict(data)


class AsyncTasksResource(BaseAsyncResource[PylonTask]):
    """Asynchronous resource for managing Pylon tasks.

    Provides async methods for listing, retrieving, creating, and updating tasks.
    """

    _endpoint = "/tasks"
    _model = PylonTask

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the async tasks resource."""
        super().__init__(transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonTask]:
        """List all tasks asynchronously.

        Args:
            limit: Number of items per page.

        Yields:
            PylonTask instances.
        """
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonTask.from_pylon_dict,
        )
        async for task in paginator:
            yield task

    async def get(self, task_id: str) -> PylonTask:
        """Get a specific task by ID asynchronously.

        Args:
            task_id: The task ID.

        Returns:
            The PylonTask instance.
        """
        response = await self._get(f"{self._endpoint}/{task_id}")
        data = response.get("data", response)
        return PylonTask.from_pylon_dict(data)

    async def create(
        self,
        *,
        title: str,
        issue_id: str | None = None,
        assignee_id: str | None = None,
        **kwargs: Any,
    ) -> PylonTask:
        """Create a new task asynchronously.

        Args:
            title: Task title/description.
            issue_id: ID of the issue to attach the task to.
            assignee_id: ID of the user to assign the task to.
            **kwargs: Additional fields.

        Returns:
            The created PylonTask instance.
        """
        data: dict[str, Any] = {"title": title, **kwargs}
        if issue_id:
            data["issue_id"] = issue_id
        if assignee_id:
            data["assignee_id"] = assignee_id
        response = await self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonTask.from_pylon_dict(result)

    async def update(self, task_id: str, **kwargs: Any) -> PylonTask:
        """Update an existing task asynchronously.

        Args:
            task_id: The task ID to update.
            **kwargs: Fields to update.

        Returns:
            The updated PylonTask instance.
        """
        response = await self._patch(f"{self._endpoint}/{task_id}", data=kwargs)
        data = response.get("data", response)
        return PylonTask.from_pylon_dict(data)
