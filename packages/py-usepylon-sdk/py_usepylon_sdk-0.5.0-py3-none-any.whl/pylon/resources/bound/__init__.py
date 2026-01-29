"""Bound resource classes for nested API endpoints.

This package contains resource classes that are bound to parent entities,
enabling access to sub-resources like account activities or issue messages.
"""

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
from pylon.resources.bound.issue_attachments import (
    IssueAttachmentsAsyncResource,
    IssueAttachmentsSyncResource,
)
from pylon.resources.bound.issue_messages import (
    IssueMessagesAsyncResource,
    IssueMessagesSyncResource,
)

__all__ = [
    # Account sub-resources
    "AccountActivitiesSyncResource",
    "AccountActivitiesAsyncResource",
    "AccountFilesSyncResource",
    "AccountFilesAsyncResource",
    "AccountHighlightsSyncResource",
    "AccountHighlightsAsyncResource",
    # Issue sub-resources
    "IssueMessagesSyncResource",
    "IssueMessagesAsyncResource",
    "IssueAttachmentsSyncResource",
    "IssueAttachmentsAsyncResource",
]
