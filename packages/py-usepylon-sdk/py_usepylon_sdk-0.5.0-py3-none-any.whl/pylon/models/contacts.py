"""Pydantic models for Pylon contact entities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from pylon.models.base import PylonCustomFieldValue, PylonReference


class PylonContact(BaseModel):
    """Pylon contact entity (read-only for matching).

    Represents a customer contact in Pylon.

    Attributes:
        id: Unique identifier for the contact.
        name: Contact name.
        email: Primary email address.
        emails: List of all email addresses.
        account: Reference to the associated account.
        custom_fields: Custom field values keyed by slug.
        portal_role: Role in the customer portal.
        avatar_url: URL to the contact's avatar image.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(description="Unique identifier for the contact")
    name: str = Field(description="Contact name")
    email: str | None = Field(
        default=None,
        description="Primary email address",
    )
    emails: list[str] = Field(
        default_factory=list,
        description="List of all email addresses",
    )
    account: PylonReference | None = Field(
        default=None,
        description="Reference to the associated account",
    )
    custom_fields: dict[str, PylonCustomFieldValue] = Field(
        default_factory=dict,
        description="Custom field values keyed by slug",
    )
    portal_role: str | None = Field(
        default=None,
        description="Role in the customer portal",
    )
    avatar_url: str | None = Field(
        default=None,
        description="URL to the contact's avatar",
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonContact:
        """Create a PylonContact from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonContact instance.
        """
        # Make a copy to avoid mutating input
        data = data.copy()

        # Convert custom_fields to PylonCustomFieldValue objects
        if "custom_fields" in data and data["custom_fields"]:
            custom_fields = {}
            for key, value in data["custom_fields"].items():
                if isinstance(value, dict):
                    custom_fields[key] = PylonCustomFieldValue.model_validate(value)
                else:
                    custom_fields[key] = PylonCustomFieldValue(value=str(value))
            data["custom_fields"] = custom_fields

        return cls.model_validate(data)

    def get_salesforce_contact_id(self, sf_client: Any = None) -> str | None:
        """Extract Salesforce Contact ID from custom fields.

        Uses the Pylon custom field 'contact.salesforce.Contact_ID_for_Pylon__c'
        which contains the Salesforce Contact ID.

        If no ID is found in custom fields and a Salesforce client is provided,
        attempts to find the contact by email address in Salesforce.

        Args:
            sf_client: Optional Salesforce client for email-based fallback lookup.

        Returns:
            Salesforce Contact ID (18-character ID) if found, None otherwise.
        """
        # Try new field name first (API slug format)
        if "contact.salesforce.Contact_ID_for_Pylon__c" in self.custom_fields:
            field_value = self.custom_fields[
                "contact.salesforce.Contact_ID_for_Pylon__c"
            ]
            if field_value.value:
                return field_value.value

        # Fall back to old field name for backwards compatibility
        if "contact_crm_id" in self.custom_fields:
            field_value = self.custom_fields["contact_crm_id"]
            if field_value.value:
                return field_value.value

        # Email-based fallback
        if sf_client and self.email:
            try:
                safe_email = self.email.replace("'", "\\'")
                query = f"SELECT Id FROM Contact WHERE Email = '{safe_email}' LIMIT 1"
                result = sf_client.query(query)
                if result.get("totalSize", 0) > 0:
                    contact_id: str = result["records"][0]["Id"]
                    return contact_id
            except Exception:
                pass

        return None
