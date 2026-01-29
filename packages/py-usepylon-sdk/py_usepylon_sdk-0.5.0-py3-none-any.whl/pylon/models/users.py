"""Pydantic models for Pylon user entities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PylonUser(BaseModel):
    """Pylon user entity (read-only for matching).

    Represents a user (team member) in the Pylon workspace.

    Attributes:
        id: Unique identifier for the user.
        name: Display name of the user.
        status: User status ("active", "out_of_office", etc.).
        email: Primary email address.
        emails: List of all email addresses.
        role_id: The user's role ID.
        avatar_url: URL to the user's avatar image.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(description="Unique identifier for the user")
    name: str = Field(description="Display name of the user")
    status: str = Field(description="User status: 'active', 'out_of_office', etc.")
    email: str = Field(description="Primary email address")
    emails: list[str] = Field(
        default_factory=list,
        description="List of all email addresses",
    )
    role_id: str = Field(description="The user's role ID")
    avatar_url: str | None = Field(
        default=None,
        description="URL to the user's avatar image",
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonUser:
        """Create a PylonUser from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonUser instance.
        """
        return cls.model_validate(data)
