"""Pydantic models for Pylon team entities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PylonTeamMember(BaseModel):
    """Team member reference.

    A minimal representation of a user within a team.

    Attributes:
        id: Unique identifier for the user.
        email: Email address of the user.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(description="Unique identifier for the user")
    email: str = Field(description="Email address of the user")


class PylonTeam(BaseModel):
    """Pylon team entity (read-only for matching).

    Represents a team in the Pylon workspace.

    Attributes:
        id: Unique identifier for the team.
        name: Team name.
        users: List of team members.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(description="Unique identifier for the team")
    name: str = Field(description="Team name")
    users: list[PylonTeamMember] = Field(
        default_factory=list,
        description="List of team members",
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonTeam:
        """Create a PylonTeam from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonTeam instance.
        """
        return cls.model_validate(data)
