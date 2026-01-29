"""Pydantic models for Pylon file entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from pylon.models.base import PylonReference


class PylonFile(BaseModel):
    """Pylon file entity.

    Represents a file associated with an account.

    Attributes:
        id: Unique identifier for the file.
        filename: Name of the file.
        url: URL to download the file.
        content_type: MIME type of the file.
        size: Size of the file in bytes.
        account: Reference to the associated account.
        uploaded_by: Reference to the user who uploaded the file.
        created_at: When the file was uploaded.
        description: Optional description of the file.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(description="Unique identifier for the file")
    filename: str = Field(description="Name of the file")
    url: str = Field(description="URL to download the file")
    content_type: str | None = Field(
        default=None,
        description="MIME type of the file",
    )
    size: int | None = Field(
        default=None,
        description="Size of the file in bytes",
    )
    account: PylonReference | None = Field(
        default=None,
        description="Reference to the associated account",
    )
    uploaded_by: PylonReference | None = Field(
        default=None,
        description="Reference to the user who uploaded the file",
    )
    created_at: datetime = Field(description="When the file was uploaded")
    description: str | None = Field(
        default=None,
        description="Optional description of the file",
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonFile:
        """Create a PylonFile from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonFile instance.
        """
        return cls.model_validate(data)
