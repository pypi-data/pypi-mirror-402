"""Tags resource for the Pylon SDK."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

from pylon.models import PylonTag
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class TagsResource(BaseSyncResource[PylonTag]):
    """Synchronous resource for managing Pylon tags."""

    _endpoint = "/tags"
    _model = PylonTag

    def __init__(self, transport: SyncHTTPTransport) -> None:
        super().__init__(transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonTag]:
        """List all tags."""
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonTag.from_pylon_dict,
        )
        yield from paginator.iter()

    def get(self, tag_id: str) -> PylonTag:
        """Get a specific tag by ID.

        Args:
            tag_id: The tag ID.

        Returns:
            The PylonTag instance.
        """
        response = self._get(f"{self._endpoint}/{tag_id}")
        data = response.get("data", response)
        return PylonTag.from_pylon_dict(data)

    def create(
        self,
        *,
        name: str,
        color: str | None = None,
        **kwargs: Any,
    ) -> PylonTag:
        """Create a new tag.

        Args:
            name: Tag name/value.
            color: Hex color for the tag.
            **kwargs: Additional fields.

        Returns:
            The created PylonTag instance.
        """
        data: dict[str, Any] = {"name": name, **kwargs}
        if color:
            data["hex_color"] = color
        response = self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonTag.from_pylon_dict(result)


class AsyncTagsResource(BaseAsyncResource[PylonTag]):
    """Asynchronous resource for managing Pylon tags."""

    _endpoint = "/tags"
    _model = PylonTag

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        super().__init__(transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonTag]:
        """List all tags asynchronously."""
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonTag.from_pylon_dict,
        )
        async for tag in paginator:
            yield tag

    async def get(self, tag_id: str) -> PylonTag:
        """Get a specific tag by ID asynchronously.

        Args:
            tag_id: The tag ID.

        Returns:
            The PylonTag instance.
        """
        response = await self._get(f"{self._endpoint}/{tag_id}")
        data = response.get("data", response)
        return PylonTag.from_pylon_dict(data)

    async def create(
        self,
        *,
        name: str,
        color: str | None = None,
        **kwargs: Any,
    ) -> PylonTag:
        """Create a new tag asynchronously.

        Args:
            name: Tag name/value.
            color: Hex color for the tag.
            **kwargs: Additional fields.

        Returns:
            The created PylonTag instance.
        """
        data: dict[str, Any] = {"name": name, **kwargs}
        if color:
            data["hex_color"] = color
        response = await self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonTag.from_pylon_dict(result)
