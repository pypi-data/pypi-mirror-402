"""Base resource classes for the Pylon SDK.

This module provides the foundational resource classes that define
the interface for interacting with Pylon API endpoints.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport

# Type variable for Pydantic model types
T = TypeVar("T", bound=BaseModel)


class BaseSyncResource(ABC, Generic[T]):
    """Base class for synchronous API resources.

    Provides common methods for CRUD operations on API resources.
    Subclasses should define the endpoint and model type.
    """

    _endpoint: str
    _model: type[T]

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the resource.

        Args:
            transport: The HTTP transport to use for requests.
        """
        self._transport = transport

    def _get(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        return self._transport.request("GET", endpoint, params=params)

    def _post(
        self,
        endpoint: str,
        *,
        data: dict[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request.

        Args:
            endpoint: API endpoint path.
            data: Request body data.
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        return self._transport.request("POST", endpoint, json=data, params=params)

    def _patch(
        self,
        endpoint: str,
        *,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a PATCH request.

        Args:
            endpoint: API endpoint path.
            data: Request body data.

        Returns:
            Parsed JSON response.
        """
        return self._transport.request("PATCH", endpoint, json=data)

    def _delete(
        self,
        endpoint: str,
    ) -> dict[str, Any]:
        """Make a DELETE request.

        Args:
            endpoint: API endpoint path.

        Returns:
            Parsed JSON response.
        """
        return self._transport.request("DELETE", endpoint)

    def _parse_single(self, data: dict[str, Any]) -> T:
        """Parse a single entity from API response.

        Handles responses wrapped in 'data' key.

        Args:
            data: Raw API response.

        Returns:
            Parsed model instance.
        """
        entity_data = data.get("data", data)
        return self._model.model_validate(entity_data)

    def _parse_list(self, data: dict[str, Any]) -> list[T]:
        """Parse a list of entities from API response.

        Args:
            data: Raw API response with 'data' list.

        Returns:
            List of parsed model instances.
        """
        items = data.get("data", [])
        return [self._model.model_validate(item) for item in items]


class BaseAsyncResource(ABC, Generic[T]):
    """Base class for asynchronous API resources.

    Provides common async methods for CRUD operations on API resources.
    Subclasses should define the endpoint and model type.
    """

    _endpoint: str
    _model: type[T]

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the resource.

        Args:
            transport: The async HTTP transport to use for requests.
        """
        self._transport = transport

    async def _get(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an async GET request.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        return await self._transport.arequest("GET", endpoint, params=params)

    async def _post(
        self,
        endpoint: str,
        *,
        data: dict[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an async POST request.

        Args:
            endpoint: API endpoint path.
            data: Request body data.
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        return await self._transport.arequest(
            "POST", endpoint, json=data, params=params
        )

    async def _patch(
        self,
        endpoint: str,
        *,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an async PATCH request.

        Args:
            endpoint: API endpoint path.
            data: Request body data.

        Returns:
            Parsed JSON response.
        """
        return await self._transport.arequest("PATCH", endpoint, json=data)

    async def _delete(
        self,
        endpoint: str,
    ) -> dict[str, Any]:
        """Make an async DELETE request.

        Args:
            endpoint: API endpoint path.

        Returns:
            Parsed JSON response.
        """
        return await self._transport.arequest("DELETE", endpoint)

    def _parse_single(self, data: dict[str, Any]) -> T:
        """Parse a single entity from API response.

        Handles responses wrapped in 'data' key.

        Args:
            data: Raw API response.

        Returns:
            Parsed model instance.
        """
        entity_data = data.get("data", data)
        return self._model.model_validate(entity_data)

    def _parse_list(self, data: dict[str, Any]) -> list[T]:
        """Parse a list of entities from API response.

        Args:
            data: Raw API response with 'data' list.

        Returns:
            List of parsed model instances.
        """
        items = data.get("data", [])
        return [self._model.model_validate(item) for item in items]
