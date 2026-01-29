"""Pagination utilities for the Pylon SDK.

This module provides iterator-based pagination for efficient memory usage
when retrieving large datasets from the Pylon API.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel

from pylon.models import PylonPagination

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport

T = TypeVar("T", bound=BaseModel)


class SyncPaginator(Generic[T]):
    """Synchronous paginator for API results.

    Provides an iterator interface for paginated API responses,
    automatically fetching additional pages as needed.

    Example:
        paginator = SyncPaginator(
            transport=transport,
            endpoint="/issues",
            model=PylonIssue,
        )
        for issue in paginator.iter():
            print(issue.title)
    """

    def __init__(
        self,
        *,
        transport: SyncHTTPTransport,
        endpoint: str,
        model: type[T],
        params: Mapping[str, Any] | None = None,
        page_size: int = 100,
        parser: Callable[[dict[str, Any]], T] | None = None,
    ) -> None:
        """Initialize the paginator.

        Args:
            transport: HTTP transport for making requests.
            endpoint: API endpoint to paginate.
            model: Pydantic model for parsing items.
            params: Additional query parameters.
            page_size: Number of items per page.
            parser: Optional custom parser function.
        """
        self._transport = transport
        self._endpoint = endpoint
        self._model = model
        self._params = dict(params or {})
        self._params.setdefault("limit", page_size)
        self._parser = parser
        self._cursor: str | None = None
        self._exhausted = False

    def iter(self) -> Iterator[T]:
        """Iterate over all paginated results.

        Yields:
            Parsed model instances.
        """
        cursor = None

        while True:
            params = dict(self._params)
            if cursor:
                params["cursor"] = cursor

            response = self._transport.request("GET", self._endpoint, params=params)

            items = response.get("data", [])
            for item in items:
                if self._parser:
                    yield self._parser(item)
                else:
                    yield self._model.model_validate(item)

            # Check pagination
            pagination_data = response.get("pagination")
            if not pagination_data:
                break

            pagination = PylonPagination.model_validate(pagination_data)
            if not pagination.has_next_page:
                break

            cursor = pagination.cursor

    def collect(self) -> list[T]:
        """Collect all paginated results into a list.

        Returns:
            A list containing all items from all pages.

        Example:
            all_issues = client.issues.list().collect()
        """
        return list(self.iter())


class AsyncPaginator(Generic[T]):
    """Asynchronous paginator for API results.

    Provides an async iterator interface for paginated API responses,
    automatically fetching additional pages as needed.

    Example:
        paginator = AsyncPaginator(
            transport=transport,
            endpoint="/issues",
            model=PylonIssue,
        )
        async for issue in paginator:
            print(issue.title)
    """

    def __init__(
        self,
        *,
        transport: AsyncHTTPTransport,
        endpoint: str,
        model: type[T],
        params: Mapping[str, Any] | None = None,
        page_size: int = 100,
        parser: Callable[[dict[str, Any]], T] | None = None,
    ) -> None:
        """Initialize the async paginator.

        Args:
            transport: Async HTTP transport for making requests.
            endpoint: API endpoint to paginate.
            model: Pydantic model for parsing items.
            params: Additional query parameters.
            page_size: Number of items per page.
            parser: Optional custom parser function.
        """
        self._transport = transport
        self._endpoint = endpoint
        self._model = model
        self._params = dict(params or {})
        self._params.setdefault("limit", page_size)
        self._parser = parser

    def __aiter__(self) -> AsyncIterator[T]:
        """Return the async iterator."""
        return self.aiter()

    async def aiter(self) -> AsyncIterator[T]:
        """Iterate asynchronously over all paginated results.

        Yields:
            Parsed model instances.
        """
        cursor = None

        while True:
            params = dict(self._params)
            if cursor:
                params["cursor"] = cursor

            response = await self._transport.arequest(
                "GET", self._endpoint, params=params
            )

            items = response.get("data", [])
            for item in items:
                if self._parser:
                    yield self._parser(item)
                else:
                    yield self._model.model_validate(item)

            # Check pagination
            pagination_data = response.get("pagination")
            if not pagination_data:
                break

            pagination = PylonPagination.model_validate(pagination_data)
            if not pagination.has_next_page:
                break

            cursor = pagination.cursor

    async def collect(self) -> list[T]:
        """Collect all paginated results into a list.

        Returns:
            A list containing all items from all pages.

        Example:
            all_issues = await client.issues.list().collect()
        """
        return [item async for item in self.aiter()]
