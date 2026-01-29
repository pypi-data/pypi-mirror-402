"""Ticket forms resource for the Pylon SDK.

This module provides resource classes for interacting with the
Pylon Ticket Forms API endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING

from pylon.models.ticket_forms import PylonTicketForm
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class TicketFormsResource(BaseSyncResource[PylonTicketForm]):
    """Synchronous resource for managing Pylon ticket forms.

    Provides methods for listing and retrieving ticket form definitions.
    Ticket forms are read-only through the API.
    """

    _endpoint = "/ticket_forms"
    _model = PylonTicketForm

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the ticket forms resource."""
        super().__init__(transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonTicketForm]:
        """List all ticket forms.

        Args:
            limit: Number of items per page.

        Yields:
            PylonTicketForm instances.
        """
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonTicketForm.from_pylon_dict,
        )
        yield from paginator.iter()

    def get(self, form_id: str) -> PylonTicketForm:
        """Get a specific ticket form by ID.

        Args:
            form_id: The ticket form ID.

        Returns:
            The PylonTicketForm instance.
        """
        response = self._get(f"{self._endpoint}/{form_id}")
        data = response.get("data", response)
        return PylonTicketForm.from_pylon_dict(data)


class AsyncTicketFormsResource(BaseAsyncResource[PylonTicketForm]):
    """Asynchronous resource for managing Pylon ticket forms.

    Provides async methods for listing and retrieving ticket form definitions.
    Ticket forms are read-only through the API.
    """

    _endpoint = "/ticket_forms"
    _model = PylonTicketForm

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the async ticket forms resource."""
        super().__init__(transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonTicketForm]:
        """List all ticket forms asynchronously.

        Args:
            limit: Number of items per page.

        Yields:
            PylonTicketForm instances.
        """
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonTicketForm.from_pylon_dict,
        )
        async for form in paginator:
            yield form

    async def get(self, form_id: str) -> PylonTicketForm:
        """Get a specific ticket form by ID asynchronously.

        Args:
            form_id: The ticket form ID.

        Returns:
            The PylonTicketForm instance.
        """
        response = await self._get(f"{self._endpoint}/{form_id}")
        data = response.get("data", response)
        return PylonTicketForm.from_pylon_dict(data)
