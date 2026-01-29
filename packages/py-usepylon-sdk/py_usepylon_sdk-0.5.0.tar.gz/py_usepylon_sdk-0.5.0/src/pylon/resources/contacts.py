"""Contacts resource for the Pylon SDK."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

from pylon.models import PylonContact
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class ContactsResource(BaseSyncResource[PylonContact]):
    """Synchronous resource for managing Pylon contacts."""

    _endpoint = "/contacts"
    _model = PylonContact

    def __init__(self, transport: SyncHTTPTransport) -> None:
        super().__init__(transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonContact]:
        """List all contacts."""
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonContact.from_pylon_dict,
        )
        yield from paginator.iter()

    def get(self, contact_id: str) -> PylonContact:
        """Get a specific contact by ID."""
        response = self._get(f"{self._endpoint}/{contact_id}")
        data = response.get("data", response)
        return PylonContact.from_pylon_dict(data)

    def search(
        self,
        query: str,
        *,
        limit: int = 100,
    ) -> Iterator[PylonContact]:
        """Search for contacts.

        Args:
            query: Search query (name, email, or company).
            limit: Maximum number of results.

        Yields:
            Matching PylonContact instances.
        """
        payload: dict[str, Any] = {"query": query, "limit": limit}
        response = self._post(f"{self._endpoint}/search", data=payload)
        items = response.get("data", [])
        for item in items:
            yield PylonContact.from_pylon_dict(item)

        while response.get("pagination", {}).get("has_next_page"):
            cursor = response["pagination"]["cursor"]
            payload["cursor"] = cursor
            response = self._post(f"{self._endpoint}/search", data=payload)
            items = response.get("data", [])
            for item in items:
                yield PylonContact.from_pylon_dict(item)

    def create(
        self,
        *,
        name: str,
        email: str,
        portal_role: str | None = None,
        **kwargs: Any,
    ) -> PylonContact:
        """Create a new contact.

        Args:
            name: Full name of the contact.
            email: Contact email address.
            portal_role: Role in customer portal (admin, member, viewer).
            **kwargs: Additional fields.

        Returns:
            The created PylonContact instance.
        """
        data: dict[str, Any] = {"name": name, "email": email, **kwargs}
        if portal_role:
            data["portal_role"] = portal_role
        response = self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonContact.from_pylon_dict(result)

    def update(self, contact_id: str, **kwargs: Any) -> PylonContact:
        """Update a contact.

        Args:
            contact_id: The contact ID to update.
            **kwargs: Fields to update.

        Returns:
            The updated PylonContact instance.
        """
        response = self._patch(f"{self._endpoint}/{contact_id}", data=kwargs)
        data = response.get("data", response)
        return PylonContact.from_pylon_dict(data)


class AsyncContactsResource(BaseAsyncResource[PylonContact]):
    """Asynchronous resource for managing Pylon contacts."""

    _endpoint = "/contacts"
    _model = PylonContact

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        super().__init__(transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonContact]:
        """List all contacts asynchronously."""
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonContact.from_pylon_dict,
        )
        async for contact in paginator:
            yield contact

    async def get(self, contact_id: str) -> PylonContact:
        """Get a specific contact by ID asynchronously."""
        response = await self._get(f"{self._endpoint}/{contact_id}")
        data = response.get("data", response)
        return PylonContact.from_pylon_dict(data)

    async def search(
        self,
        query: str,
        *,
        limit: int = 100,
    ) -> AsyncIterator[PylonContact]:
        """Search for contacts asynchronously.

        Args:
            query: Search query (name, email, or company).
            limit: Maximum number of results.

        Yields:
            Matching PylonContact instances.
        """
        payload: dict[str, Any] = {"query": query, "limit": limit}
        response = await self._post(f"{self._endpoint}/search", data=payload)
        items = response.get("data", [])
        for item in items:
            yield PylonContact.from_pylon_dict(item)

        while response.get("pagination", {}).get("has_next_page"):
            cursor = response["pagination"]["cursor"]
            payload["cursor"] = cursor
            response = await self._post(f"{self._endpoint}/search", data=payload)
            items = response.get("data", [])
            for item in items:
                yield PylonContact.from_pylon_dict(item)

    async def create(
        self,
        *,
        name: str,
        email: str,
        portal_role: str | None = None,
        **kwargs: Any,
    ) -> PylonContact:
        """Create a new contact asynchronously.

        Args:
            name: Full name of the contact.
            email: Contact email address.
            portal_role: Role in customer portal (admin, member, viewer).
            **kwargs: Additional fields.

        Returns:
            The created PylonContact instance.
        """
        data: dict[str, Any] = {"name": name, "email": email, **kwargs}
        if portal_role:
            data["portal_role"] = portal_role
        response = await self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonContact.from_pylon_dict(result)

    async def update(self, contact_id: str, **kwargs: Any) -> PylonContact:
        """Update a contact asynchronously.

        Args:
            contact_id: The contact ID to update.
            **kwargs: Fields to update.

        Returns:
            The updated PylonContact instance.
        """
        response = await self._patch(f"{self._endpoint}/{contact_id}", data=kwargs)
        data = response.get("data", response)
        return PylonContact.from_pylon_dict(data)
