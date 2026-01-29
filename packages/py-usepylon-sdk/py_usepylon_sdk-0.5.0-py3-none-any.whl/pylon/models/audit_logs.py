"""Pydantic models for Pylon audit log entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from pylon.models.base import PylonReference


class PylonAuditLog(BaseModel):
    """Pylon audit log entry.

    Audit logs track actions taken within the Pylon system.

    Attributes:
        id: Unique identifier for the log entry.
        action: Type of action performed.
        resource_type: Type of resource affected.
        resource_id: ID of the affected resource.
        actor: Reference to the user who performed the action.
        timestamp: When the action occurred.
        details: Additional details about the action.
        ip_address: IP address of the actor.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier")
    action: str = Field(description="Action type")
    resource_type: str = Field(description="Type of resource affected")
    resource_id: str | None = Field(default=None, description="ID of affected resource")
    actor: PylonReference | None = Field(default=None, description="Reference to actor")
    timestamp: datetime = Field(description="When action occurred")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional details"
    )
    ip_address: str | None = Field(default=None, description="Actor IP address")

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonAuditLog:
        """Create a PylonAuditLog from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonAuditLog instance.
        """
        return cls.model_validate(data)
