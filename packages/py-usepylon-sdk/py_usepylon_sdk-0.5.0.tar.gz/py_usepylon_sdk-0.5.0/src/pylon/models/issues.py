"""Pydantic models for Pylon issue entities."""

from __future__ import annotations

from collections.abc import Coroutine
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from pylon.models.base import (
    PylonCustomFieldValue,
    PylonReference,
    RichModelMixin,
)

if TYPE_CHECKING:
    from pylon._client import AsyncPylonClient, PylonClient
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport
    from pylon.models.messages import PylonMessage
    from pylon.resources.bound.issue_attachments import (
        IssueAttachmentsAsyncResource,
        IssueAttachmentsSyncResource,
    )
    from pylon.resources.bound.issue_messages import (
        IssueMessagesAsyncResource,
        IssueMessagesSyncResource,
    )


class PylonSlackInfoForIssues(BaseModel):
    """Slack-specific information for issues.

    Contains metadata about the Slack message that created this issue.

    Attributes:
        message_ts: Slack message timestamp.
        channel_id: Slack channel ID.
        workspace_id: Slack workspace ID.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    message_ts: str = Field(description="Slack message timestamp")
    channel_id: str = Field(description="Slack channel ID")
    workspace_id: str = Field(description="Slack workspace ID")


class PylonIssue(RichModelMixin, BaseModel):
    """Pylon issue entity with rich methods.

    Represents a support issue/ticket in Pylon with convenience methods
    for common operations like resolving, assigning, and adding messages.

    Rich Methods (require client binding):
        add_message(): Add a customer-facing message.
        add_internal_note(): Add an internal note.
        resolve(): Mark the issue as resolved.
        reopen(): Reopen a resolved issue.
        assign_to(): Assign to a user.
        assign_to_team(): Assign to a team.
        snooze(): Snooze until a specific time.
        add_tags(): Add tags to the issue.
        remove_tags(): Remove tags from the issue.
        refresh(): Refresh issue data from the API.

    Attributes:
        id: Unique identifier for the issue.
        number: Human-readable issue number.
        title: Issue title.
        link: URL to the issue in Pylon.
        body_html: HTML content of the issue body.
        state: Issue state ("new", "waiting_on_customer", etc.).
        account: Reference to the associated account.
        assignee: Reference to the assigned user.
        requester: Reference to the requester contact.
        team: Reference to the assigned team.
        tags: List of tag IDs.
        custom_fields: Custom field values keyed by slug.
        first_response_time: Time of first response.
        resolution_time: Time of resolution.
        latest_message_time: Time of most recent message.
        created_at: When the issue was created.
        customer_portal_visible: Whether visible in customer portal.
        source: Source channel ("slack", "email", "form").
        slack: Slack-specific information (if source is slack).
        type: Issue type ("Conversation", "Ticket").
        number_of_touches: Number of interactions.
        first_response_seconds: Seconds until first response.
        business_hours_first_response_seconds: Business hours until first response.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    # Private attributes for sub-resource access
    _sync_transport: SyncHTTPTransport | None = PrivateAttr(default=None)
    _async_transport: AsyncHTTPTransport | None = PrivateAttr(default=None)
    # Private attributes for client binding (from RichModelMixin)
    _sync_client: PylonClient | None = PrivateAttr(default=None)
    _async_client: AsyncPylonClient | None = PrivateAttr(default=None)

    id: str = Field(description="Unique identifier for the issue")
    number: int = Field(description="Human-readable issue number")
    title: str = Field(description="Issue title")
    link: str = Field(description="URL to the issue in Pylon")
    body_html: str = Field(description="HTML content of the issue body")
    state: str = Field(description="Issue state")
    account: PylonReference | None = Field(
        default=None,
        description="Reference to the associated account",
    )
    assignee: PylonReference | None = Field(
        default=None,
        description="Reference to the assigned user",
    )
    requester: PylonReference | None = Field(
        default=None,
        description="Reference to the requester contact",
    )
    team: PylonReference | None = Field(
        default=None,
        description="Reference to the assigned team",
    )
    tags: list[str] | None = Field(default=None, description="List of tag IDs")
    custom_fields: dict[str, PylonCustomFieldValue] = Field(
        default_factory=dict,
        description="Custom field values keyed by slug",
    )
    first_response_time: datetime | None = Field(
        default=None,
        description="Time of first response",
    )
    resolution_time: datetime | None = Field(
        default=None,
        description="Time of resolution",
    )
    latest_message_time: datetime = Field(description="Time of most recent message")
    created_at: datetime = Field(description="When the issue was created")
    customer_portal_visible: bool = Field(
        description="Whether visible in customer portal"
    )
    source: str = Field(description="Source channel: 'slack', 'email', 'form'")
    slack: PylonSlackInfoForIssues | None = Field(
        default=None,
        description="Slack-specific information",
    )
    type: str = Field(description="Issue type: 'Conversation', 'Ticket'")
    number_of_touches: int = Field(description="Number of interactions")
    first_response_seconds: int | None = Field(
        default=None,
        description="Seconds until first response",
    )
    business_hours_first_response_seconds: int | None = Field(
        default=None,
        description="Business hours until first response",
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonIssue:
        """Create a PylonIssue from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonIssue instance.
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

    def _with_sync_transport(self, transport: SyncHTTPTransport) -> PylonIssue:
        """Inject a sync transport for sub-resource access.

        Args:
            transport: The sync HTTP transport.

        Returns:
            Self for chaining.
        """
        self._sync_transport = transport
        return self

    def _with_async_transport(self, transport: AsyncHTTPTransport) -> PylonIssue:
        """Inject an async transport for sub-resource access.

        Args:
            transport: The async HTTP transport.

        Returns:
            Self for chaining.
        """
        self._async_transport = transport
        return self

    @property
    def messages(self) -> IssueMessagesSyncResource | IssueMessagesAsyncResource:
        """Access messages sub-resource.

        Returns:
            A bound resource for accessing messages.

        Raises:
            RuntimeError: If no transport has been injected.
        """
        from pylon.resources.bound.issue_messages import (
            IssueMessagesAsyncResource,
            IssueMessagesSyncResource,
        )

        if self._sync_transport:
            return IssueMessagesSyncResource(self._sync_transport, self.id)
        elif self._async_transport:
            return IssueMessagesAsyncResource(self._async_transport, self.id)
        raise RuntimeError(
            "No transport available. Issue was not fetched through client."
        )

    @property
    def attachments(
        self,
    ) -> IssueAttachmentsSyncResource | IssueAttachmentsAsyncResource:
        """Access attachments sub-resource.

        Returns:
            A bound resource for accessing attachments.

        Raises:
            RuntimeError: If no transport has been injected.
        """
        from pylon.resources.bound.issue_attachments import (
            IssueAttachmentsAsyncResource,
            IssueAttachmentsSyncResource,
        )

        if self._sync_transport:
            return IssueAttachmentsSyncResource(self._sync_transport, self.id)
        elif self._async_transport:
            return IssueAttachmentsAsyncResource(self._async_transport, self.id)
        raise RuntimeError(
            "No transport available. Issue was not fetched through client."
        )

    # -------------------------------------------------------------------------
    # Rich Methods - require client binding via _bind_client()
    # -------------------------------------------------------------------------

    def add_message(
        self, content: str, *, is_private: bool = False
    ) -> PylonMessage | Coroutine[Any, Any, PylonMessage]:
        """Add a message to this issue.

        Args:
            content: The message content (supports markdown).
            is_private: If True, creates an internal note instead of
                a customer-visible message.

        Returns:
            The created PylonMessage (sync) or a coroutine (async).

        Raises:
            ClientNotBoundError: If no client is bound to this model.
        """
        self._ensure_client("add_message")
        if self._sync_client:
            return self._sync_client.messages.create(
                issue_id=self.id, content=content, is_private=is_private
            )
        # Async path
        return self._async_client.messages.create(  # type: ignore[union-attr]
            issue_id=self.id, content=content, is_private=is_private
        )

    def add_internal_note(
        self, content: str
    ) -> PylonMessage | Coroutine[Any, Any, PylonMessage]:
        """Add an internal note to this issue.

        Internal notes are only visible to team members, not customers.

        Args:
            content: The note content (supports markdown).

        Returns:
            The created PylonMessage (sync) or a coroutine (async).

        Raises:
            ClientNotBoundError: If no client is bound to this model.
        """
        return self.add_message(content, is_private=True)

    def resolve(self) -> PylonIssue | Coroutine[Any, Any, PylonIssue]:
        """Mark this issue as resolved.

        Updates the issue state to "resolved" and refreshes this model
        with the updated data from the API.

        Returns:
            Self with updated fields (sync) or a coroutine (async).

        Raises:
            ClientNotBoundError: If no client is bound to this model.
        """
        self._ensure_client("resolve")
        if self._sync_client:
            updated = self._sync_client.issues.update(self.id, state="resolved")
            self._update_from(updated)
            return self
        # Async path - return coroutine
        return self._resolve_async()

    async def _resolve_async(self) -> PylonIssue:
        """Async implementation of resolve()."""
        updated = await self._async_client.issues.update(  # type: ignore[union-attr]
            self.id, state="resolved"
        )
        self._update_from(updated)
        return self

    def reopen(self) -> PylonIssue | Coroutine[Any, Any, PylonIssue]:
        """Reopen this issue.

        Updates the issue state to "open" and refreshes this model
        with the updated data from the API.

        Returns:
            Self with updated fields (sync) or a coroutine (async).

        Raises:
            ClientNotBoundError: If no client is bound to this model.
        """
        self._ensure_client("reopen")
        if self._sync_client:
            updated = self._sync_client.issues.update(self.id, state="open")
            self._update_from(updated)
            return self
        # Async path
        return self._reopen_async()

    async def _reopen_async(self) -> PylonIssue:
        """Async implementation of reopen()."""
        updated = await self._async_client.issues.update(  # type: ignore[union-attr]
            self.id, state="open"
        )
        self._update_from(updated)
        return self

    def assign_to(self, user_id: str) -> PylonIssue | Coroutine[Any, Any, PylonIssue]:
        """Assign this issue to a user.

        Args:
            user_id: The user ID to assign the issue to.

        Returns:
            Self with updated fields (sync) or a coroutine (async).

        Raises:
            ClientNotBoundError: If no client is bound to this model.
        """
        self._ensure_client("assign_to")
        if self._sync_client:
            updated = self._sync_client.issues.update(self.id, assignee_id=user_id)
            self._update_from(updated)
            return self
        # Async path
        return self._assign_to_async(user_id)

    async def _assign_to_async(self, user_id: str) -> PylonIssue:
        """Async implementation of assign_to()."""
        updated = await self._async_client.issues.update(  # type: ignore[union-attr]
            self.id, assignee_id=user_id
        )
        self._update_from(updated)
        return self

    def assign_to_team(
        self, team_id: str
    ) -> PylonIssue | Coroutine[Any, Any, PylonIssue]:
        """Assign this issue to a team.

        Args:
            team_id: The team ID to assign the issue to.

        Returns:
            Self with updated fields (sync) or a coroutine (async).

        Raises:
            ClientNotBoundError: If no client is bound to this model.
        """
        self._ensure_client("assign_to_team")
        if self._sync_client:
            updated = self._sync_client.issues.update(self.id, team_id=team_id)
            self._update_from(updated)
            return self
        # Async path
        return self._assign_to_team_async(team_id)

    async def _assign_to_team_async(self, team_id: str) -> PylonIssue:
        """Async implementation of assign_to_team()."""
        updated = await self._async_client.issues.update(  # type: ignore[union-attr]
            self.id, team_id=team_id
        )
        self._update_from(updated)
        return self

    def snooze(
        self, until: datetime | str
    ) -> PylonIssue | Coroutine[Any, Any, PylonIssue]:
        """Snooze this issue until a specific time.

        The issue will be hidden from the queue until the specified time.

        Args:
            until: When the issue should reappear. Can be a datetime object
                or an ISO 8601 formatted string.

        Returns:
            Self with updated fields (sync) or a coroutine (async).

        Raises:
            ClientNotBoundError: If no client is bound to this model.
        """
        self._ensure_client("snooze")
        if self._sync_client:
            updated = self._sync_client.issues.snooze(self.id, until=until)
            self._update_from(updated)
            return self
        # Async path
        return self._snooze_async(until)

    async def _snooze_async(self, until: datetime | str) -> PylonIssue:
        """Async implementation of snooze()."""
        updated = await self._async_client.issues.snooze(  # type: ignore[union-attr]
            self.id, until=until
        )
        self._update_from(updated)
        return self

    def add_tags(
        self, tag_ids: list[str]
    ) -> PylonIssue | Coroutine[Any, Any, PylonIssue]:
        """Add tags to this issue.

        Args:
            tag_ids: List of tag IDs to add.

        Returns:
            Self with updated fields (sync) or a coroutine (async).

        Raises:
            ClientNotBoundError: If no client is bound to this model.
        """
        self._ensure_client("add_tags")
        if self._sync_client:
            results = self._sync_client.issues.bulk_add_tags([self.id], tag_ids)
            if results:
                self._update_from(results[0])
            return self
        # Async path
        return self._add_tags_async(tag_ids)

    async def _add_tags_async(self, tag_ids: list[str]) -> PylonIssue:
        """Async implementation of add_tags()."""
        results = await self._async_client.issues.bulk_add_tags(  # type: ignore[union-attr]
            [self.id], tag_ids
        )
        if results:
            self._update_from(results[0])
        return self

    def remove_tags(
        self, tag_ids: list[str]
    ) -> PylonIssue | Coroutine[Any, Any, PylonIssue]:
        """Remove tags from this issue.

        Args:
            tag_ids: List of tag IDs to remove.

        Returns:
            Self with updated fields (sync) or a coroutine (async).

        Raises:
            ClientNotBoundError: If no client is bound to this model.
        """
        self._ensure_client("remove_tags")
        if self._sync_client:
            results = self._sync_client.issues.bulk_remove_tags([self.id], tag_ids)
            if results:
                self._update_from(results[0])
            return self
        # Async path
        return self._remove_tags_async(tag_ids)

    async def _remove_tags_async(self, tag_ids: list[str]) -> PylonIssue:
        """Async implementation of remove_tags()."""
        results = await self._async_client.issues.bulk_remove_tags(  # type: ignore[union-attr]
            [self.id], tag_ids
        )
        if results:
            self._update_from(results[0])
        return self

    def refresh(self) -> PylonIssue | Coroutine[Any, Any, PylonIssue]:
        """Refresh this issue's data from the API.

        Fetches the latest version of the issue and updates all fields
        on this model instance.

        Returns:
            Self with updated fields (sync) or a coroutine (async).

        Raises:
            ClientNotBoundError: If no client is bound to this model.
        """
        self._ensure_client("refresh")
        if self._sync_client:
            updated = self._sync_client.issues.get(self.id)
            self._update_from(updated)
            return self
        # Async path
        return self._refresh_async()

    async def _refresh_async(self) -> PylonIssue:
        """Async implementation of refresh()."""
        updated = await self._async_client.issues.get(  # type: ignore[union-attr]
            self.id
        )
        self._update_from(updated)
        return self
