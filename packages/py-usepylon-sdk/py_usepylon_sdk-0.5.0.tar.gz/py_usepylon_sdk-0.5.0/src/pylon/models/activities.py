"""Pydantic models for Pylon activity entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from pylon.models.base import PylonReference


class PylonActivity(BaseModel):
    """Pylon activity entity.

    Represents an activity record associated with an account.

    Attributes:
        id: Unique identifier for the activity.
        type: Type of activity (e.g., "email", "call", "meeting").
        description: Description of the activity.
        account: Reference to the associated account.
        actor: Reference to the user who performed the activity.
        created_at: When the activity occurred.
        metadata: Additional metadata for the activity.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(description="Unique identifier for the activity")
    type: str = Field(description="Type of activity")
    description: str | None = Field(
        default=None,
        description="Description of the activity",
    )
    account: PylonReference | None = Field(
        default=None,
        description="Reference to the associated account",
    )
    actor: PylonReference | None = Field(
        default=None,
        description="Reference to the user who performed the activity",
    )
    created_at: datetime = Field(description="When the activity occurred")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonActivity:
        """Create a PylonActivity from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonActivity instance.
        """
        return cls.model_validate(data)
