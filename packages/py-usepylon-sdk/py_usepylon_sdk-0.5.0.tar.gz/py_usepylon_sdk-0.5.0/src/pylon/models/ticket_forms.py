"""Pydantic models for Pylon ticket form entities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PylonTicketFormField(BaseModel):
    """Field definition within a ticket form.

    Attributes:
        id: Unique identifier for the field.
        name: Field name/label.
        field_type: Type of field (text, textarea, select, etc.).
        required: Whether the field is required.
        options: Options for select/multi-select fields.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Field ID")
    name: str = Field(description="Field name/label")
    field_type: str = Field(description="Field type")
    required: bool = Field(default=False, description="Whether field is required")
    options: list[str] = Field(default_factory=list, description="Field options")


class PylonTicketForm(BaseModel):
    """Pylon ticket form entity.

    Ticket forms define the fields customers see when submitting tickets.

    Attributes:
        id: Unique identifier for the form.
        name: Name of the form.
        description: Optional description shown to customers.
        fields: List of fields in the form.
        active: Whether the form is active.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier")
    name: str = Field(description="Form name")
    description: str | None = Field(default=None, description="Form description")
    fields: list[PylonTicketFormField] = Field(
        default_factory=list, description="Form fields"
    )
    active: bool = Field(default=True, description="Whether form is active")

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonTicketForm:
        """Create a PylonTicketForm from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonTicketForm instance.
        """
        return cls.model_validate(data)
