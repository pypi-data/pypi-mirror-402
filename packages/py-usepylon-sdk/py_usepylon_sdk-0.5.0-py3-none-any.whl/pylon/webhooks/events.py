"""Pydantic models for Pylon issue webhook events.

These models mirror the flattened JSON payloads sent by Pylon webhooks for
issue-related events. They are intentionally separate from the richer
`PylonIssue` API model so that the Cloud Run ingress service can validate and
normalize incoming webhook payloads while still retaining the original field
names used by Pylon.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class BaseIssueEvent(BaseModel):
    """Fields common to all Pylon issue webhook events.

    This mirrors the flattened `issue_*` keys observed in Datastore for every
    `event_type`. Numeric identifiers are modelled as `int` values for
    better type-safety; Pydantic will coerce from the string values used in the
    raw JSON payloads.
    """

    model_config = ConfigDict(extra="ignore")

    event_type: str = Field(description="Type of webhook event")
    issue_id: str = Field(description="Issue ID")
    issue_number: int = Field(description="Human-readable issue number")
    issue_title: str = Field(description="Issue title")
    issue_team_name: str = Field(description="Team name")
    issue_account_id: str = Field(description="Account ID")
    issue_account_name: str = Field(description="Account name")
    issue_requester_email: str = Field(description="Requester email")
    issue_requesteer_id: str = Field(
        description="Requester ID (NOTE: intentional double 'ee' - matches Pylon's actual webhook payload spelling)"
    )
    issue_assignee_email: str = Field(description="Assignee email")
    issue_assignee_id: str = Field(description="Assignee ID")
    issue_salesforce_account_id: str | None = Field(
        default=None,
        description="Salesforce account ID",
    )


class IssueSnapshotEvent(BaseIssueEvent):
    """Full issue snapshot fields shared by most `issue_*` events.

    Present on: `issue_new`, `issue_assigned`, `issue_field_changed`,
    `issue_status_changed`, `issue_tags_changed`, and `issue_reaction`.
    """

    issue_body: str = Field(description="Issue body content")
    issue_status: str = Field(description="Issue status")
    issue_sf_type: str = Field(description="Salesforce type")
    issue_last_message_sent_at: datetime = Field(description="Last message time")
    issue_link: str = Field(description="Link to issue")
    issue_tags: list[str] = Field(default_factory=list, description="Issue tags")
    issue_account_domains: list[str] = Field(
        default_factory=list,
        description="Account domains",
    )
    issue_attachment_urls: list[str] = Field(
        default_factory=list,
        description="Attachment URLs",
    )
    issue_custom_field_feature_mentioned: str | None = Field(
        default=None,
        description="Custom field: feature mentioned",
    )
    issue_custom_field_ide_mentioned: str | None = Field(
        default=None,
        description="Custom field: IDE mentioned",
    )
    issue_custom_field_priority: str | None = Field(
        default=None,
        description="Custom field: priority",
    )
    issue_custom_field_question_type: str | None = Field(
        default=None,
        description="Custom field: question type",
    )
    issue_custom_field_request_id_if_applicable: str | None = Field(
        default=None,
        description="Custom field: request ID",
    )
    issue_custom_field_salesforce_issue_id: str | None = Field(
        default=None,
        description="Custom field: Salesforce issue ID",
    )


class IssueNewEvent(IssueSnapshotEvent):
    """Pylon webhook event for newly-created issues."""

    event_type: Literal["issue_new"] = Field(default="issue_new")


class IssueAssignedEvent(IssueSnapshotEvent):
    """Issue assignment or reassignment event."""

    event_type: Literal["issue_assigned"] = Field(default="issue_assigned")


class IssueFieldChangedEvent(IssueSnapshotEvent):
    """Event emitted when arbitrary issue fields change."""

    event_type: Literal["issue_field_changed"] = Field(default="issue_field_changed")


class IssueStatusChangedEvent(IssueSnapshotEvent):
    """Event emitted when the issue status transitions."""

    event_type: Literal["issue_status_changed"] = Field(default="issue_status_changed")


class IssueTagsChangedEvent(IssueSnapshotEvent):
    """Event emitted when the set of tags on an issue changes."""

    event_type: Literal["issue_tags_changed"] = Field(default="issue_tags_changed")


class IssueReactionEvent(IssueSnapshotEvent):
    """Reaction activity on an issue."""

    event_type: Literal["issue_reaction"] = Field(default="issue_reaction")


class IssueMessageNewEvent(BaseIssueEvent):
    """New message added to an issue (customer-visible or internal)."""

    event_type: Literal["issue_message_new"] = Field(default="issue_message_new")
    message_id: str = Field(description="Message ID")
    message_author_id: str = Field(description="Message author ID")
    message_author_name: str = Field(description="Message author name")
    message_body_html: str = Field(description="Message body HTML")
    message_ccs: list[str] = Field(default_factory=list, description="CC recipients")
    message_is_private: bool = Field(description="Is private/internal message")
    message_sent_at: datetime = Field(description="When message was sent")


PylonWebhookEvent = Annotated[
    IssueNewEvent
    | IssueAssignedEvent
    | IssueFieldChangedEvent
    | IssueStatusChangedEvent
    | IssueTagsChangedEvent
    | IssueReactionEvent
    | IssueMessageNewEvent,
    Field(discriminator="event_type"),
]

_PYLON_WEBHOOK_EVENT_ADAPTER: TypeAdapter[PylonWebhookEvent] = TypeAdapter(
    PylonWebhookEvent
)


def parse_webhook_event(payload: dict[str, Any]) -> PylonWebhookEvent:
    """Parse a raw webhook JSON payload into a strongly-typed event model.

    Args:
        payload: Raw JSON body decoded into a Python dict.

    Returns:
        A concrete `Issue*Event` instance corresponding to `event_type`.

    Raises:
        pydantic.ValidationError: If the payload does not conform to the
            expected schema or `event_type` is unknown.
    """
    return _PYLON_WEBHOOK_EVENT_ADAPTER.validate_python(payload)
