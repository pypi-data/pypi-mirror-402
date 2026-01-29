"""Custom fields resource for the Pylon SDK.

This module provides resource classes for interacting with the
Pylon Custom Fields API endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING

from pylon.models.custom_fields import PylonCustomField
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class CustomFieldsResource(BaseSyncResource[PylonCustomField]):
    """Synchronous resource for managing Pylon custom fields.

    Provides methods for listing and retrieving custom field definitions.
    Custom fields are read-only through the API.
    """

    _endpoint = "/custom_fields"
    _model = PylonCustomField

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the custom fields resource."""
        super().__init__(transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonCustomField]:
        """List all custom field definitions.

        Args:
            limit: Number of items per page.

        Yields:
            PylonCustomField instances.
        """
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonCustomField.from_pylon_dict,
        )
        yield from paginator.iter()

    def get(self, custom_field_id: str) -> PylonCustomField:
        """Get a specific custom field by ID.

        Args:
            custom_field_id: The custom field ID.

        Returns:
            The PylonCustomField instance.
        """
        response = self._get(f"{self._endpoint}/{custom_field_id}")
        data = response.get("data", response)
        return PylonCustomField.from_pylon_dict(data)


class AsyncCustomFieldsResource(BaseAsyncResource[PylonCustomField]):
    """Asynchronous resource for managing Pylon custom fields.

    Provides async methods for listing and retrieving custom field definitions.
    Custom fields are read-only through the API.
    """

    _endpoint = "/custom_fields"
    _model = PylonCustomField

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the async custom fields resource."""
        super().__init__(transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonCustomField]:
        """List all custom field definitions asynchronously.

        Args:
            limit: Number of items per page.

        Yields:
            PylonCustomField instances.
        """
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonCustomField.from_pylon_dict,
        )
        async for field in paginator:
            yield field

    async def get(self, custom_field_id: str) -> PylonCustomField:
        """Get a specific custom field by ID asynchronously.

        Args:
            custom_field_id: The custom field ID.

        Returns:
            The PylonCustomField instance.
        """
        response = await self._get(f"{self._endpoint}/{custom_field_id}")
        data = response.get("data", response)
        return PylonCustomField.from_pylon_dict(data)
