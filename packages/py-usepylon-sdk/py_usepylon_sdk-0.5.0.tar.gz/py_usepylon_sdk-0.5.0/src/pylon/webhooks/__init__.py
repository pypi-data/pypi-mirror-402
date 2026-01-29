"""Webhook handling for the Pylon SDK.

This package provides models and utilities for processing Pylon webhook events,
including signature verification and event dispatching.

Example:
    from pylon.webhooks import WebhookHandler, IssueNewEvent

    handler = WebhookHandler(secret="your_webhook_secret")

    @handler.on("issue_new")
    def on_new_issue(event: IssueNewEvent):
        print(f"New issue: {event.issue_title}")

    # Process incoming webhook
    handler.handle(payload, headers)
"""

from pylon.webhooks.events import (
    BaseIssueEvent,
    IssueAssignedEvent,
    IssueFieldChangedEvent,
    IssueMessageNewEvent,
    IssueNewEvent,
    IssueReactionEvent,
    IssueSnapshotEvent,
    IssueStatusChangedEvent,
    IssueTagsChangedEvent,
    PylonWebhookEvent,
    parse_webhook_event,
)
from pylon.webhooks.handler import WebhookHandler

__all__ = [
    # Event models
    "BaseIssueEvent",
    "IssueSnapshotEvent",
    "IssueNewEvent",
    "IssueAssignedEvent",
    "IssueFieldChangedEvent",
    "IssueStatusChangedEvent",
    "IssueTagsChangedEvent",
    "IssueReactionEvent",
    "IssueMessageNewEvent",
    "PylonWebhookEvent",
    # Parsing
    "parse_webhook_event",
    # Handler
    "WebhookHandler",
]
