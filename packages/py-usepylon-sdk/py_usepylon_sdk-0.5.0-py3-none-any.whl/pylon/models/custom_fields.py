"""Pydantic models for Pylon custom field entities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PylonCustomFieldOption(BaseModel):
    """Option for select/multi-select custom fields.

    Attributes:
        id: Unique identifier for the option.
        value: Display value of the option.
        order: Display order of the option.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Option ID")
    value: str = Field(description="Display value")
    order: int | None = Field(default=None, description="Display order")


class PylonCustomField(BaseModel):
    """Pylon custom field definition.

    Custom fields allow extending issues and contacts with custom data.

    Attributes:
        id: Unique identifier for the custom field.
        name: Human-readable name of the field.
        slug: URL-friendly identifier for the field.
        field_type: Type of the field (text, number, select, multi_select, etc.).
        description: Optional description of the field.
        required: Whether the field is required.
        options: For select/multi_select fields, the available options.
        object_type: Type of object this field applies to (issue, contact).
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier")
    name: str = Field(description="Human-readable name")
    slug: str = Field(description="URL-friendly identifier")
    field_type: str = Field(description="Field type: text, number, select, etc.")
    description: str | None = Field(default=None, description="Field description")
    required: bool = Field(default=False, description="Whether field is required")
    options: list[PylonCustomFieldOption] = Field(
        default_factory=list,
        description="Options for select/multi_select fields",
    )
    object_type: str | None = Field(
        default=None,
        description="Object type this field applies to",
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonCustomField:
        """Create a PylonCustomField from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonCustomField instance.
        """
        return cls.model_validate(data)
