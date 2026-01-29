"""Pydantic models for Pylon attachment entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PylonAttachment(BaseModel):
    """Pylon attachment entity.

    Represents a file attachment in Pylon.

    Attributes:
        id: Unique identifier for the attachment.
        filename: Name of the attached file.
        url: URL to download the attachment.
        content_type: MIME type of the attachment.
        size: Size of the attachment in bytes.
        created_at: When the attachment was created.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(description="Unique identifier for the attachment")
    filename: str = Field(description="Name of the attached file")
    url: str = Field(description="URL to download the attachment")
    content_type: str | None = Field(
        default=None,
        description="MIME type of the attachment",
    )
    size: int | None = Field(
        default=None,
        description="Size of the attachment in bytes",
    )
    created_at: datetime = Field(description="When the attachment was created")

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonAttachment:
        """Create a PylonAttachment from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonAttachment instance.
        """
        return cls.model_validate(data)
