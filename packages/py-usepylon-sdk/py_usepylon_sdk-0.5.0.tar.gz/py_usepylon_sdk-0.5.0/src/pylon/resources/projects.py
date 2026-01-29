"""Projects resource for the Pylon SDK.

This module provides resource classes for interacting with the
Pylon Projects API endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

from pylon.models.projects import PylonProject
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class ProjectsResource(BaseSyncResource[PylonProject]):
    """Synchronous resource for managing Pylon projects.

    Provides methods for listing, retrieving, and creating projects.
    """

    _endpoint = "/projects"
    _model = PylonProject

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the projects resource."""
        super().__init__(transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonProject]:
        """List all projects.

        Args:
            limit: Number of items per page.

        Yields:
            PylonProject instances.
        """
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonProject.from_pylon_dict,
        )
        yield from paginator.iter()

    def get(self, project_id: str) -> PylonProject:
        """Get a specific project by ID.

        Args:
            project_id: The project ID.

        Returns:
            The PylonProject instance.
        """
        response = self._get(f"{self._endpoint}/{project_id}")
        data = response.get("data", response)
        return PylonProject.from_pylon_dict(data)

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        **kwargs: Any,
    ) -> PylonProject:
        """Create a new project.

        Args:
            name: Project name.
            description: Optional project description.
            **kwargs: Additional fields.

        Returns:
            The created PylonProject instance.
        """
        data: dict[str, Any] = {"name": name, **kwargs}
        if description:
            data["description"] = description
        response = self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonProject.from_pylon_dict(result)


class AsyncProjectsResource(BaseAsyncResource[PylonProject]):
    """Asynchronous resource for managing Pylon projects.

    Provides async methods for listing, retrieving, and creating projects.
    """

    _endpoint = "/projects"
    _model = PylonProject

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the async projects resource."""
        super().__init__(transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonProject]:
        """List all projects asynchronously.

        Args:
            limit: Number of items per page.

        Yields:
            PylonProject instances.
        """
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonProject.from_pylon_dict,
        )
        async for project in paginator:
            yield project

    async def get(self, project_id: str) -> PylonProject:
        """Get a specific project by ID asynchronously.

        Args:
            project_id: The project ID.

        Returns:
            The PylonProject instance.
        """
        response = await self._get(f"{self._endpoint}/{project_id}")
        data = response.get("data", response)
        return PylonProject.from_pylon_dict(data)

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        **kwargs: Any,
    ) -> PylonProject:
        """Create a new project asynchronously.

        Args:
            name: Project name.
            description: Optional project description.
            **kwargs: Additional fields.

        Returns:
            The created PylonProject instance.
        """
        data: dict[str, Any] = {"name": name, **kwargs}
        if description:
            data["description"] = description
        response = await self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonProject.from_pylon_dict(result)
