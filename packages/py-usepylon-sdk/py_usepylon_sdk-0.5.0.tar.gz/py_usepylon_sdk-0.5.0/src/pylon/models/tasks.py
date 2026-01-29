"""Pydantic models for Pylon task entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from pylon.models.base import PylonReference


class PylonTask(BaseModel):
    """Pylon task entity.

    Tasks are action items associated with issues.

    Attributes:
        id: Unique identifier for the task.
        title: Title/description of the task.
        status: Task status (pending, completed, etc.).
        due_date: Optional due date for the task.
        completed_at: When the task was completed.
        created_at: When the task was created.
        updated_at: When the task was last updated.
        issue: Reference to the parent issue.
        assignee: Reference to the assigned user.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier")
    title: str = Field(description="Task title/description")
    status: str = Field(default="pending", description="Task status")
    due_date: datetime | None = Field(default=None, description="Due date")
    completed_at: datetime | None = Field(
        default=None, description="When task was completed"
    )
    created_at: datetime | None = Field(
        default=None, description="When task was created"
    )
    updated_at: datetime | None = Field(
        default=None, description="When task was last updated"
    )
    issue: PylonReference | None = Field(
        default=None, description="Reference to parent issue"
    )
    assignee: PylonReference | None = Field(
        default=None, description="Reference to assigned user"
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonTask:
        """Create a PylonTask from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonTask instance.
        """
        return cls.model_validate(data)
