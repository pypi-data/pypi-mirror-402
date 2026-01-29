"""Pydantic models for Pylon user role entities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PylonUserRole(BaseModel):
    """Pylon user role entity.

    User roles define permissions and access levels for team members.

    Attributes:
        id: Unique identifier for the role.
        name: Name of the role.
        description: Optional description of the role.
        permissions: List of permission strings.
        is_default: Whether this is the default role for new users.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier")
    name: str = Field(description="Role name")
    description: str | None = Field(default=None, description="Role description")
    permissions: list[str] = Field(
        default_factory=list, description="Permission strings"
    )
    is_default: bool = Field(
        default=False, description="Whether this is the default role"
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonUserRole:
        """Create a PylonUserRole from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonUserRole instance.
        """
        return cls.model_validate(data)
