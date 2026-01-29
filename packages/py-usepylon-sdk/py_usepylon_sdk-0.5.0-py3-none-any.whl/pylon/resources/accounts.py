"""Accounts resource for the Pylon SDK.

This module provides resource classes for interacting with the
Pylon Accounts API endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

from pylon.models import PylonAccount
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class AccountsResource(BaseSyncResource[PylonAccount]):
    """Synchronous resource for managing Pylon accounts.

    Provides methods for listing and retrieving accounts via the Pylon API.

    Example:
        client = PylonClient(api_key="...")

        # List all accounts
        for account in client.accounts.list():
            print(f"{account.name}")

        # Get a specific account
        account = client.accounts.get("account_123")
    """

    _endpoint = "/accounts"
    _model = PylonAccount

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the accounts resource.

        Args:
            transport: The HTTP transport to use for requests.
        """
        super().__init__(transport)

    def _inject_transport(self, account: PylonAccount) -> PylonAccount:
        """Inject transport into account for sub-resource access."""
        return account._with_sync_transport(self._transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonAccount]:
        """List all accounts.

        Args:
            limit: Number of items per page.

        Yields:
            PylonAccount instances with transport for sub-resource access.
        """
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonAccount.from_pylon_dict,
        )
        for account in paginator.iter():
            yield self._inject_transport(account)

    def get(self, account_id: str) -> PylonAccount:
        """Get a specific account by ID.

        Args:
            account_id: The account ID.

        Returns:
            The PylonAccount instance with transport for sub-resource access.
        """
        response = self._get(f"{self._endpoint}/{account_id}")
        data = response.get("data", response)
        account = PylonAccount.from_pylon_dict(data)
        return self._inject_transport(account)

    def search(
        self,
        field: str,
        value: str,
        *,
        limit: int = 100,
    ) -> Iterator[PylonAccount]:
        """Search accounts by custom field.

        Args:
            field: The custom field slug to search.
            value: The value to match.
            limit: Maximum number of results.

        Yields:
            Matching PylonAccount instances with transport for sub-resource access.
        """
        payload = {
            "filter": {
                "field": field,
                "operator": "equals",
                "value": value,
            },
            "limit": limit,
        }

        response = self._post(f"{self._endpoint}/search", data=payload)
        items = response.get("data", [])
        for item in items:
            yield self._inject_transport(PylonAccount.from_pylon_dict(item))

        # Handle pagination
        while response.get("pagination", {}).get("has_next_page"):
            cursor = response["pagination"]["cursor"]
            payload["cursor"] = cursor
            response = self._post(f"{self._endpoint}/search", data=payload)
            items = response.get("data", [])
            for item in items:
                yield self._inject_transport(PylonAccount.from_pylon_dict(item))

    def create(
        self,
        *,
        name: str,
        domain: str | None = None,
        **kwargs: Any,
    ) -> PylonAccount:
        """Create a new account.

        Args:
            name: Account name.
            domain: Primary domain for the account.
            **kwargs: Additional fields.

        Returns:
            The created PylonAccount instance with transport for sub-resource access.
        """
        data: dict[str, Any] = {"name": name, **kwargs}
        if domain:
            data["domain"] = domain
        response = self._post(self._endpoint, data=data)
        result = response.get("data", response)
        account = PylonAccount.from_pylon_dict(result)
        return self._inject_transport(account)

    def update(self, account_id: str, **kwargs: Any) -> PylonAccount:
        """Update an account.

        Args:
            account_id: The account ID to update.
            **kwargs: Fields to update.

        Returns:
            The updated PylonAccount instance with transport for sub-resource access.
        """
        response = self._patch(f"{self._endpoint}/{account_id}", data=kwargs)
        data = response.get("data", response)
        account = PylonAccount.from_pylon_dict(data)
        return self._inject_transport(account)


class AsyncAccountsResource(BaseAsyncResource[PylonAccount]):
    """Asynchronous resource for managing Pylon accounts.

    Provides async methods for listing and retrieving accounts via the Pylon API.

    Example:
        async with AsyncPylonClient(api_key="...") as client:
            # List all accounts
            async for account in client.accounts.list():
                print(f"{account.name}")

            # Get a specific account
            account = await client.accounts.get("account_123")
    """

    _endpoint = "/accounts"
    _model = PylonAccount

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the async accounts resource.

        Args:
            transport: The async HTTP transport to use for requests.
        """
        super().__init__(transport)

    def _inject_transport(self, account: PylonAccount) -> PylonAccount:
        """Inject transport into account for sub-resource access."""
        return account._with_async_transport(self._transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonAccount]:
        """List all accounts asynchronously.

        Args:
            limit: Number of items per page.

        Yields:
            PylonAccount instances with transport for sub-resource access.
        """
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonAccount.from_pylon_dict,
        )
        async for account in paginator:
            yield self._inject_transport(account)

    async def get(self, account_id: str) -> PylonAccount:
        """Get a specific account by ID asynchronously.

        Args:
            account_id: The account ID.

        Returns:
            The PylonAccount instance with transport for sub-resource access.
        """
        response = await self._get(f"{self._endpoint}/{account_id}")
        data = response.get("data", response)
        account = PylonAccount.from_pylon_dict(data)
        return self._inject_transport(account)

    async def search(
        self,
        field: str,
        value: str,
        *,
        limit: int = 100,
    ) -> AsyncIterator[PylonAccount]:
        """Search accounts by custom field asynchronously.

        Args:
            field: The custom field slug to search.
            value: The value to match.
            limit: Maximum number of results.

        Yields:
            Matching PylonAccount instances with transport for sub-resource access.
        """
        payload: dict[str, Any] = {
            "filter": {
                "field": field,
                "operator": "equals",
                "value": value,
            },
            "limit": limit,
        }

        response = await self._post(f"{self._endpoint}/search", data=payload)
        items = response.get("data", [])
        for item in items:
            yield self._inject_transport(PylonAccount.from_pylon_dict(item))

        # Handle pagination
        while response.get("pagination", {}).get("has_next_page"):
            cursor = response["pagination"]["cursor"]
            payload["cursor"] = cursor
            response = await self._post(f"{self._endpoint}/search", data=payload)
            items = response.get("data", [])
            for item in items:
                yield self._inject_transport(PylonAccount.from_pylon_dict(item))

    async def create(
        self,
        *,
        name: str,
        domain: str | None = None,
        **kwargs: Any,
    ) -> PylonAccount:
        """Create a new account asynchronously.

        Args:
            name: Account name.
            domain: Primary domain for the account.
            **kwargs: Additional fields.

        Returns:
            The created PylonAccount instance with transport for sub-resource access.
        """
        data: dict[str, Any] = {"name": name, **kwargs}
        if domain:
            data["domain"] = domain
        response = await self._post(self._endpoint, data=data)
        result = response.get("data", response)
        account = PylonAccount.from_pylon_dict(result)
        return self._inject_transport(account)

    async def update(self, account_id: str, **kwargs: Any) -> PylonAccount:
        """Update an account asynchronously.

        Args:
            account_id: The account ID to update.
            **kwargs: Fields to update.

        Returns:
            The updated PylonAccount instance with transport for sub-resource access.
        """
        response = await self._patch(f"{self._endpoint}/{account_id}", data=kwargs)
        data = response.get("data", response)
        account = PylonAccount.from_pylon_dict(data)
        return self._inject_transport(account)
