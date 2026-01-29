"""Pydantic models for Pylon account entities."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from pylon.models.base import PylonCustomFieldValue, PylonReference

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport
    from pylon.resources.bound.account_activities import (
        AccountActivitiesAsyncResource,
        AccountActivitiesSyncResource,
    )
    from pylon.resources.bound.account_files import (
        AccountFilesAsyncResource,
        AccountFilesSyncResource,
    )
    from pylon.resources.bound.account_highlights import (
        AccountHighlightsAsyncResource,
        AccountHighlightsSyncResource,
    )


class PylonAccount(BaseModel):
    """Pylon account entity (read-only for matching).

    Represents a customer account in Pylon.

    Attributes:
        id: Unique identifier for the account.
        name: Account name.
        owner: Reference to the account owner (user).
        domain: Primary domain for the account.
        domains: List of all domains associated with the account.
        primary_domain: The primary domain.
        type: Account type.
        channels: List of communication channels.
        created_at: When the account was created.
        tags: List of tag IDs applied to the account.
        custom_fields: Custom field values keyed by slug.
        latest_customer_activity_time: Most recent customer activity.
        external_ids: External system identifiers.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    # Private attributes for sub-resource access
    _sync_transport: SyncHTTPTransport | None = PrivateAttr(default=None)
    _async_transport: AsyncHTTPTransport | None = PrivateAttr(default=None)

    id: str = Field(description="Unique identifier for the account")
    name: str = Field(description="Account name")
    owner: PylonReference | None = Field(
        default=None,
        description="Reference to the account owner",
    )
    domain: str | None = Field(default=None, description="Primary domain")
    domains: list[str] | None = Field(
        default=None,
        description="List of all domains",
    )
    primary_domain: str | None = Field(default=None, description="Primary domain")
    type: str = Field(description="Account type")
    channels: list[Any] = Field(
        default_factory=list,
        description="Communication channels",
    )
    created_at: datetime = Field(description="When the account was created")
    tags: list[str] | None = Field(
        default=None,
        description="List of tag IDs",
    )
    custom_fields: dict[str, PylonCustomFieldValue] = Field(
        default_factory=dict,
        description="Custom field values keyed by slug",
    )
    latest_customer_activity_time: datetime | None = Field(
        default=None,
        description="Most recent customer activity",
    )
    external_ids: dict[str, str] | None = Field(
        default=None,
        description="External system identifiers",
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonAccount:
        """Create a PylonAccount from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonAccount instance.
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

        # Handle empty string for datetime fields
        if (
            "latest_customer_activity_time" in data
            and data["latest_customer_activity_time"] == ""
        ):
            data["latest_customer_activity_time"] = None

        return cls.model_validate(data)

    def get_salesforce_account_id(self) -> str | None:
        """Extract Salesforce Account ID from custom fields.

        Uses the Pylon custom field 'account.salesforce.Account_ID_for_Pylon__c'
        which contains the Salesforce Account ID.

        Returns:
            Salesforce Account ID (18-character ID) if found, None otherwise.
        """
        # Try new field name first (API slug format)
        if "account.salesforce.Account_ID_for_Pylon__c" in self.custom_fields:
            field_value = self.custom_fields[
                "account.salesforce.Account_ID_for_Pylon__c"
            ]
            if field_value.value:
                return field_value.value

        # Fall back to old field name for backwards compatibility
        if "account_crm_id" in self.custom_fields:
            field_value = self.custom_fields["account_crm_id"]
            if field_value.value:
                return field_value.value

        return None

    def get_is_enterprise(self) -> bool | None:
        """Extract is_enterprise flag from custom fields.

        Uses the Pylon custom field 'account.is_enterprise' which indicates
        whether this is an enterprise account.

        Returns:
            True if enterprise account, False if not, None if field not found.
        """
        if "account.is_enterprise" in self.custom_fields:
            field_value = self.custom_fields["account.is_enterprise"]
            if field_value.value:
                value_str = str(field_value.value).lower()
                if value_str in ("true", "1", "yes"):
                    return True
                elif value_str in ("false", "0", "no"):
                    return False
        return None

    def _with_sync_transport(self, transport: SyncHTTPTransport) -> PylonAccount:
        """Inject a sync transport for sub-resource access.

        Args:
            transport: The sync HTTP transport.

        Returns:
            Self for chaining.
        """
        self._sync_transport = transport
        return self

    def _with_async_transport(self, transport: AsyncHTTPTransport) -> PylonAccount:
        """Inject an async transport for sub-resource access.

        Args:
            transport: The async HTTP transport.

        Returns:
            Self for chaining.
        """
        self._async_transport = transport
        return self

    @property
    def activities(
        self,
    ) -> AccountActivitiesSyncResource | AccountActivitiesAsyncResource:
        """Access activities sub-resource.

        Returns:
            A bound resource for accessing activities.

        Raises:
            RuntimeError: If no transport has been injected.
        """
        from pylon.resources.bound.account_activities import (
            AccountActivitiesAsyncResource,
            AccountActivitiesSyncResource,
        )

        if self._sync_transport:
            return AccountActivitiesSyncResource(self._sync_transport, self.id)
        elif self._async_transport:
            return AccountActivitiesAsyncResource(self._async_transport, self.id)
        raise RuntimeError(
            "No transport available. Account was not fetched through client."
        )

    @property
    def files(self) -> AccountFilesSyncResource | AccountFilesAsyncResource:
        """Access files sub-resource.

        Returns:
            A bound resource for accessing files.

        Raises:
            RuntimeError: If no transport has been injected.
        """
        from pylon.resources.bound.account_files import (
            AccountFilesAsyncResource,
            AccountFilesSyncResource,
        )

        if self._sync_transport:
            return AccountFilesSyncResource(self._sync_transport, self.id)
        elif self._async_transport:
            return AccountFilesAsyncResource(self._async_transport, self.id)
        raise RuntimeError(
            "No transport available. Account was not fetched through client."
        )

    @property
    def highlights(
        self,
    ) -> AccountHighlightsSyncResource | AccountHighlightsAsyncResource:
        """Access highlights sub-resource.

        Returns:
            A bound resource for accessing highlights.

        Raises:
            RuntimeError: If no transport has been injected.
        """
        from pylon.resources.bound.account_highlights import (
            AccountHighlightsAsyncResource,
            AccountHighlightsSyncResource,
        )

        if self._sync_transport:
            return AccountHighlightsSyncResource(self._sync_transport, self.id)
        elif self._async_transport:
            return AccountHighlightsAsyncResource(self._async_transport, self.id)
        raise RuntimeError(
            "No transport available. Account was not fetched through client."
        )
