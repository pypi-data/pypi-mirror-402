"""Pydantic models for Pylon current user (me) entity."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from pylon.models.base import PylonReference


class PylonMe(BaseModel):
    """Current authenticated user information.

    Represents the user associated with the API key.

    Attributes:
        id: Unique identifier for the user.
        name: User's display name.
        email: Primary email address.
        emails: All email addresses for the user.
        role: Reference to the user's role.
        avatar_url: URL to the user's avatar image.
        status: User status (active, inactive).
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier")
    name: str = Field(description="Display name")
    email: str | None = Field(default=None, description="Primary email address")
    emails: list[str] = Field(default_factory=list, description="All email addresses")
    role: PylonReference | None = Field(default=None, description="User role reference")
    avatar_url: str | None = Field(default=None, description="Avatar URL")
    status: str = Field(default="active", description="User status")

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonMe:
        """Create a PylonMe from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonMe instance.
        """
        return cls.model_validate(data)
