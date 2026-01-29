"""User roles resource for the Pylon SDK.

This module provides resource classes for interacting with the
Pylon User Roles API endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING

from pylon.models.user_roles import PylonUserRole
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class UserRolesResource(BaseSyncResource[PylonUserRole]):
    """Synchronous resource for managing Pylon user roles.

    Provides methods for listing and retrieving user role definitions.
    User roles are read-only through the API.
    """

    _endpoint = "/user_roles"
    _model = PylonUserRole

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the user roles resource."""
        super().__init__(transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonUserRole]:
        """List all user roles.

        Args:
            limit: Number of items per page.

        Yields:
            PylonUserRole instances.
        """
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonUserRole.from_pylon_dict,
        )
        yield from paginator.iter()

    def get(self, role_id: str) -> PylonUserRole:
        """Get a specific user role by ID.

        Args:
            role_id: The user role ID.

        Returns:
            The PylonUserRole instance.
        """
        response = self._get(f"{self._endpoint}/{role_id}")
        data = response.get("data", response)
        return PylonUserRole.from_pylon_dict(data)


class AsyncUserRolesResource(BaseAsyncResource[PylonUserRole]):
    """Asynchronous resource for managing Pylon user roles.

    Provides async methods for listing and retrieving user role definitions.
    User roles are read-only through the API.
    """

    _endpoint = "/user_roles"
    _model = PylonUserRole

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the async user roles resource."""
        super().__init__(transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonUserRole]:
        """List all user roles asynchronously.

        Args:
            limit: Number of items per page.

        Yields:
            PylonUserRole instances.
        """
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonUserRole.from_pylon_dict,
        )
        async for role in paginator:
            yield role

    async def get(self, role_id: str) -> PylonUserRole:
        """Get a specific user role by ID asynchronously.

        Args:
            role_id: The user role ID.

        Returns:
            The PylonUserRole instance.
        """
        response = await self._get(f"{self._endpoint}/{role_id}")
        data = response.get("data", response)
        return PylonUserRole.from_pylon_dict(data)
