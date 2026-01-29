"""Bound resource classes for nested API endpoints.

This module provides base classes for resources that are bound to a parent
entity, enabling access to nested API endpoints like /accounts/{id}/activities.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import AsyncIterator, Callable, Iterator, Mapping
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel

from pylon.models.pagination import PylonPagination

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport

T = TypeVar("T", bound=BaseModel)


class BoundSyncResource(ABC, Generic[T]):
    """Base class for synchronous resources bound to a parent entity.

    Provides common methods for accessing sub-resources under a parent,
    e.g., /accounts/{account_id}/activities.

    Attributes:
        _parent_path: The parent resource path (e.g., "accounts").
        _resource_name: The sub-resource name (e.g., "activities").
        _model: The Pydantic model class for parsing items.
    """

    _parent_path: str
    _resource_name: str
    _model: type[T]
    _parser: Callable[[dict[str, Any]], T] | None = None

    def __init__(self, transport: SyncHTTPTransport, parent_id: str) -> None:
        """Initialize the bound resource.

        Args:
            transport: The HTTP transport to use for requests.
            parent_id: The ID of the parent entity.
        """
        self._transport = transport
        self._parent_id = parent_id

    @property
    def _base_path(self) -> str:
        """Build the base path for this sub-resource."""
        return f"/{self._parent_path}/{self._parent_id}/{self._resource_name}"

    def _get(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        return self._transport.request("GET", endpoint, params=params)

    def _post(
        self,
        endpoint: str,
        *,
        data: dict[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        return self._transport.request("POST", endpoint, json=data, params=params)

    def _parse_single(self, data: dict[str, Any]) -> T:
        """Parse a single entity from API response."""
        entity_data = data.get("data", data)
        if self._parser:
            return self._parser(entity_data)
        return self._model.model_validate(entity_data)

    def _parse_list(self, data: dict[str, Any]) -> list[T]:
        """Parse a list of entities from API response."""
        items = data.get("data", [])
        if self._parser:
            return [self._parser(item) for item in items]
        return [self._model.model_validate(item) for item in items]

    def list(self, *, limit: int = 100) -> Iterator[T]:
        """List sub-resources.

        Args:
            limit: Number of items per page.

        Yields:
            Parsed model instances.
        """
        cursor: str | None = None

        while True:
            params: dict[str, Any] = {"limit": limit}
            if cursor:
                params["cursor"] = cursor

            response = self._get(self._base_path, params=params)
            items = response.get("data", [])

            for item in items:
                if self._parser:
                    yield self._parser(item)
                else:
                    yield self._model.model_validate(item)

            pagination_data = response.get("pagination")
            if not pagination_data:
                break

            pagination = PylonPagination.model_validate(pagination_data)
            if not pagination.has_next_page:
                break

            cursor = pagination.cursor
            # Guard against empty cursor with has_next_page=True (API edge case)
            if not cursor:
                break

    def get(self, resource_id: str) -> T:
        """Get a specific sub-resource by ID.

        Args:
            resource_id: The sub-resource ID.

        Returns:
            The parsed model instance.
        """
        response = self._get(f"{self._base_path}/{resource_id}")
        return self._parse_single(response)

    def create(self, **kwargs: Any) -> T:
        """Create a new sub-resource.

        Args:
            **kwargs: Fields for the new resource.

        Returns:
            The created model instance.
        """
        response = self._post(self._base_path, data=kwargs)
        return self._parse_single(response)


class BoundAsyncResource(ABC, Generic[T]):
    """Base class for asynchronous resources bound to a parent entity.

    Provides async methods for accessing sub-resources under a parent,
    e.g., /accounts/{account_id}/activities.
    """

    _parent_path: str
    _resource_name: str
    _model: type[T]
    _parser: Callable[[dict[str, Any]], T] | None = None

    def __init__(self, transport: AsyncHTTPTransport, parent_id: str) -> None:
        """Initialize the async bound resource.

        Args:
            transport: The async HTTP transport to use for requests.
            parent_id: The ID of the parent entity.
        """
        self._transport = transport
        self._parent_id = parent_id

    @property
    def _base_path(self) -> str:
        """Build the base path for this sub-resource."""
        return f"/{self._parent_path}/{self._parent_id}/{self._resource_name}"

    async def _get(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an async GET request."""
        return await self._transport.arequest("GET", endpoint, params=params)

    async def _post(
        self,
        endpoint: str,
        *,
        data: dict[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an async POST request."""
        return await self._transport.arequest(
            "POST", endpoint, json=data, params=params
        )

    def _parse_single(self, data: dict[str, Any]) -> T:
        """Parse a single entity from API response."""
        entity_data = data.get("data", data)
        if self._parser:
            return self._parser(entity_data)
        return self._model.model_validate(entity_data)

    def _parse_list(self, data: dict[str, Any]) -> list[T]:
        """Parse a list of entities from API response."""
        items = data.get("data", [])
        if self._parser:
            return [self._parser(item) for item in items]
        return [self._model.model_validate(item) for item in items]

    async def list(self, *, limit: int = 100) -> AsyncIterator[T]:
        """List sub-resources asynchronously.

        Args:
            limit: Number of items per page.

        Yields:
            Parsed model instances.
        """
        cursor: str | None = None

        while True:
            params: dict[str, Any] = {"limit": limit}
            if cursor:
                params["cursor"] = cursor

            response = await self._get(self._base_path, params=params)
            items = response.get("data", [])

            for item in items:
                if self._parser:
                    yield self._parser(item)
                else:
                    yield self._model.model_validate(item)

            pagination_data = response.get("pagination")
            if not pagination_data:
                break

            pagination = PylonPagination.model_validate(pagination_data)
            if not pagination.has_next_page:
                break

            cursor = pagination.cursor
            # Guard against empty cursor with has_next_page=True (API edge case)
            if not cursor:
                break

    async def get(self, resource_id: str) -> T:
        """Get a specific sub-resource by ID asynchronously.

        Args:
            resource_id: The sub-resource ID.

        Returns:
            The parsed model instance.
        """
        response = await self._get(f"{self._base_path}/{resource_id}")
        return self._parse_single(response)

    async def create(self, **kwargs: Any) -> T:
        """Create a new sub-resource asynchronously.

        Args:
            **kwargs: Fields for the new resource.

        Returns:
            The created model instance.
        """
        response = await self._post(self._base_path, data=kwargs)
        return self._parse_single(response)
