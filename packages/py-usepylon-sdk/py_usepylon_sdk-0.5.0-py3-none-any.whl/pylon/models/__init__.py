"""Pydantic models for Pylon API entities.

This package contains all the data models used to represent Pylon API
resources. All models use Pydantic v2 for validation and serialization.
"""

from pylon.models.accounts import PylonAccount
from pylon.models.activities import PylonActivity
from pylon.models.attachments import PylonAttachment
from pylon.models.audit_logs import PylonAuditLog
from pylon.models.base import PylonCustomFieldValue, PylonReference
from pylon.models.contacts import PylonContact
from pylon.models.custom_fields import PylonCustomField, PylonCustomFieldOption
from pylon.models.files import PylonFile
from pylon.models.highlights import PylonHighlight
from pylon.models.issues import PylonIssue, PylonSlackInfoForIssues
from pylon.models.knowledge_base import PylonKnowledgeBase, PylonKnowledgeBaseArticle
from pylon.models.me import PylonMe
from pylon.models.messages import (
    PylonEmailInfo,
    PylonMessage,
    PylonMessageAuthor,
    PylonMessageAuthorContact,
    PylonMessageAuthorUser,
    PylonSlackInfoForMessages,
)
from pylon.models.pagination import PylonPagination, PylonResponse
from pylon.models.projects import PylonProject
from pylon.models.tags import PylonTag
from pylon.models.tasks import PylonTask
from pylon.models.teams import PylonTeam, PylonTeamMember
from pylon.models.ticket_forms import PylonTicketForm, PylonTicketFormField
from pylon.models.user_roles import PylonUserRole
from pylon.models.users import PylonUser

__all__ = [
    # Base models
    "PylonReference",
    "PylonCustomFieldValue",
    # Account models
    "PylonAccount",
    # Activity models (sub-resource)
    "PylonActivity",
    # Audit log models
    "PylonAuditLog",
    # Contact models
    "PylonContact",
    # File models (sub-resource)
    "PylonFile",
    # Highlight models (sub-resource)
    "PylonHighlight",
    # Custom field models
    "PylonCustomField",
    "PylonCustomFieldOption",
    # Issue models
    "PylonIssue",
    "PylonSlackInfoForIssues",
    # Me (current user) models
    "PylonMe",
    # Message models
    "PylonMessage",
    "PylonMessageAuthor",
    "PylonMessageAuthorContact",
    "PylonMessageAuthorUser",
    "PylonEmailInfo",
    "PylonSlackInfoForMessages",
    # Attachment models
    "PylonAttachment",
    # Knowledge base models
    "PylonKnowledgeBase",
    "PylonKnowledgeBaseArticle",
    # Project models
    "PylonProject",
    # Task models
    "PylonTask",
    # Ticket form models
    "PylonTicketForm",
    "PylonTicketFormField",
    # User models
    "PylonUser",
    # User role models
    "PylonUserRole",
    # Team models
    "PylonTeam",
    "PylonTeamMember",
    # Tag models
    "PylonTag",
    # Pagination models
    "PylonPagination",
    "PylonResponse",
]
