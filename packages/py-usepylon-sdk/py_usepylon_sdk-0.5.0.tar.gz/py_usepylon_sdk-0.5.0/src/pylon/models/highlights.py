"""Pydantic models for Pylon highlight entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from pylon.models.base import PylonReference


class PylonHighlight(BaseModel):
    """Pylon highlight entity.

    Represents a highlight/note associated with an account.

    Attributes:
        id: Unique identifier for the highlight.
        title: Title of the highlight.
        content: Content of the highlight.
        account: Reference to the associated account.
        author: Reference to the user who created the highlight.
        created_at: When the highlight was created.
        updated_at: When the highlight was last updated.
        tags: List of tags applied to the highlight.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(description="Unique identifier for the highlight")
    title: str | None = Field(
        default=None,
        description="Title of the highlight",
    )
    content: str = Field(description="Content of the highlight")
    account: PylonReference | None = Field(
        default=None,
        description="Reference to the associated account",
    )
    author: PylonReference | None = Field(
        default=None,
        description="Reference to the user who created the highlight",
    )
    created_at: datetime = Field(description="When the highlight was created")
    updated_at: datetime | None = Field(
        default=None,
        description="When the highlight was last updated",
    )
    tags: list[str] | None = Field(
        default=None,
        description="List of tags applied to the highlight",
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonHighlight:
        """Create a PylonHighlight from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonHighlight instance.
        """
        return cls.model_validate(data)
