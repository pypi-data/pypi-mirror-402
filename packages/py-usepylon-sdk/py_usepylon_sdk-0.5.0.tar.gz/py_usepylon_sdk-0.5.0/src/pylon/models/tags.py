"""Pydantic models for Pylon tag entities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PylonTag(BaseModel):
    """Pylon tag entity.

    Tags are used to categorize issues and accounts in Pylon.

    Attributes:
        id: Unique identifier for the tag.
        value: The tag value/name.
        object_type: Type of object this tag applies to ("account" or "issue").
        hex_color: Optional hex color code for the tag.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(description="Unique identifier for the tag")
    value: str = Field(description="The tag value/name")
    object_type: str = Field(description="Type of object: 'account' or 'issue'")
    hex_color: str | None = Field(
        default=None,
        description="Optional hex color code for the tag",
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonTag:
        """Create a PylonTag from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonTag instance.
        """
        return cls.model_validate(data)
