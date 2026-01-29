"""Teams resource for the Pylon SDK."""

from __future__ import annotations

import builtins
from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

from pylon.models import PylonTeam
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class TeamsResource(BaseSyncResource[PylonTeam]):
    """Synchronous resource for managing Pylon teams."""

    _endpoint = "/teams"
    _model = PylonTeam

    def __init__(self, transport: SyncHTTPTransport) -> None:
        super().__init__(transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonTeam]:
        """List all teams."""
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonTeam.from_pylon_dict,
        )
        yield from paginator.iter()

    def get(self, team_id: str) -> PylonTeam:
        """Get a specific team by ID.

        Args:
            team_id: The team ID.

        Returns:
            The PylonTeam instance.
        """
        response = self._get(f"{self._endpoint}/{team_id}")
        data = response.get("data", response)
        return PylonTeam.from_pylon_dict(data)

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        members: builtins.list[str] | None = None,
        **kwargs: Any,
    ) -> PylonTeam:
        """Create a new team.

        Args:
            name: Team name.
            description: Team description.
            members: List of user IDs or emails to add.
            **kwargs: Additional fields.

        Returns:
            The created PylonTeam instance.
        """
        data: dict[str, Any] = {"name": name, **kwargs}
        if description:
            data["description"] = description
        if members:
            data["members"] = members
        response = self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonTeam.from_pylon_dict(result)


class AsyncTeamsResource(BaseAsyncResource[PylonTeam]):
    """Asynchronous resource for managing Pylon teams."""

    _endpoint = "/teams"
    _model = PylonTeam

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        super().__init__(transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonTeam]:
        """List all teams asynchronously."""
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonTeam.from_pylon_dict,
        )
        async for team in paginator:
            yield team

    async def get(self, team_id: str) -> PylonTeam:
        """Get a specific team by ID asynchronously.

        Args:
            team_id: The team ID.

        Returns:
            The PylonTeam instance.
        """
        response = await self._get(f"{self._endpoint}/{team_id}")
        data = response.get("data", response)
        return PylonTeam.from_pylon_dict(data)

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        members: builtins.list[str] | None = None,
        **kwargs: Any,
    ) -> PylonTeam:
        """Create a new team asynchronously.

        Args:
            name: Team name.
            description: Team description.
            members: List of user IDs or emails to add.
            **kwargs: Additional fields.

        Returns:
            The created PylonTeam instance.
        """
        data: dict[str, Any] = {"name": name, **kwargs}
        if description:
            data["description"] = description
        if members:
            data["members"] = members
        response = await self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonTeam.from_pylon_dict(result)
