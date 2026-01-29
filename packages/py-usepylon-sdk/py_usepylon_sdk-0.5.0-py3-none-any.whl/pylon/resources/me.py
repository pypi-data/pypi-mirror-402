"""Me (current user) resource for the Pylon SDK.

This module provides resource classes for accessing the
current authenticated user's information.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pylon.models.me import PylonMe
from pylon.resources._base import BaseAsyncResource, BaseSyncResource

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class MeResource(BaseSyncResource[PylonMe]):
    """Synchronous resource for accessing current user information.

    Provides method for retrieving the authenticated user's profile.
    """

    _endpoint = "/me"
    _model = PylonMe

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the me resource."""
        super().__init__(transport)

    def get(self) -> PylonMe:
        """Get the current authenticated user's information.

        Returns:
            The PylonMe instance representing the current user.
        """
        response = self._get(self._endpoint)
        data = response.get("data", response)
        return PylonMe.from_pylon_dict(data)


class AsyncMeResource(BaseAsyncResource[PylonMe]):
    """Asynchronous resource for accessing current user information.

    Provides async method for retrieving the authenticated user's profile.
    """

    _endpoint = "/me"
    _model = PylonMe

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the async me resource."""
        super().__init__(transport)

    async def get(self) -> PylonMe:
        """Get the current authenticated user's information asynchronously.

        Returns:
            The PylonMe instance representing the current user.
        """
        response = await self._get(self._endpoint)
        data = response.get("data", response)
        return PylonMe.from_pylon_dict(data)
