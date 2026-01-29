"""Pydantic models for Pylon API pagination."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PylonPagination(BaseModel):
    """Pagination information from Pylon API.

    The Pylon API uses cursor-based pagination. This model represents
    the pagination metadata returned in API responses.

    Attributes:
        cursor: The cursor to use for fetching the next page.
        has_next_page: Whether there are more pages to fetch.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    cursor: str | None = Field(
        default=None,
        description="Cursor for the next page",
    )
    has_next_page: bool = Field(
        default=False,
        description="Whether more pages are available",
    )


class PylonResponse(BaseModel):
    """Generic Pylon API response wrapper.

    Most Pylon API endpoints return responses in this format, with
    a data array, optional pagination info, and a request ID.

    Attributes:
        data: List of items returned by the API.
        pagination: Optional pagination information.
        request_id: Unique identifier for this API request.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    data: list[dict[str, Any]] = Field(description="List of items from the API")
    pagination: PylonPagination | None = Field(
        default=None,
        description="Pagination information",
    )
    request_id: str = Field(description="Unique request identifier")
