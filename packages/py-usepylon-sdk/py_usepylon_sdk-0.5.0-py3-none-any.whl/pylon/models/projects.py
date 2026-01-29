"""Pydantic models for Pylon project entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from pylon.models.base import PylonReference


class PylonProject(BaseModel):
    """Pylon project entity.

    Projects are used to group and organize issues.

    Attributes:
        id: Unique identifier for the project.
        name: Name of the project.
        description: Optional description.
        status: Project status (active, archived, etc.).
        created_at: When the project was created.
        updated_at: When the project was last updated.
        owner: Reference to the project owner.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier")
    name: str = Field(description="Project name")
    description: str | None = Field(default=None, description="Project description")
    status: str = Field(default="active", description="Project status")
    created_at: datetime | None = Field(
        default=None, description="When project was created"
    )
    updated_at: datetime | None = Field(
        default=None, description="When project was last updated"
    )
    owner: PylonReference | None = Field(
        default=None, description="Reference to project owner"
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonProject:
        """Create a PylonProject from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonProject instance.
        """
        return cls.model_validate(data)
