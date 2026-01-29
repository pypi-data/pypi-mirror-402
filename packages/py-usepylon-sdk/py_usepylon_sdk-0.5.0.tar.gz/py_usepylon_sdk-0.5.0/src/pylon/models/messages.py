"""Pydantic models for Pylon message entities."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from urllib.parse import unquote, urlparse

from pydantic import BaseModel, ConfigDict, Field


class PylonMessageAuthorContact(BaseModel):
    """Contact information in message author.

    Attributes:
        id: Contact ID.
        email: Contact email address.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Contact ID")
    email: str | None = Field(default=None, description="Contact email address")


class PylonMessageAuthorUser(BaseModel):
    """User information in message author.

    Attributes:
        id: User ID.
        email: User email address.
        name: User display name.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="User ID")
    email: str | None = Field(default=None, description="User email address")
    name: str | None = Field(default=None, description="User display name")


class PylonMessageAuthor(BaseModel):
    """Author of a Pylon message (can be contact or user).

    Attributes:
        contact: Contact info if author is a contact.
        user: User info if author is a user.
        name: Display name of the author.
        avatar_url: URL to the author's avatar.
    """

    model_config = ConfigDict(extra="ignore")

    contact: PylonMessageAuthorContact | None = Field(
        default=None,
        description="Contact info if author is a contact",
    )
    user: PylonMessageAuthorUser | None = Field(
        default=None,
        description="User info if author is a user",
    )
    name: str | None = Field(default=None, description="Display name")
    avatar_url: str | None = Field(default=None, description="Avatar URL")


class PylonEmailInfo(BaseModel):
    """Email-specific information for messages.

    Attributes:
        from_email: Sender email address.
        to_emails: List of recipient email addresses.
        cc_emails: List of CC email addresses.
        bcc_emails: List of BCC email addresses.
    """

    model_config = ConfigDict(extra="ignore")

    from_email: str | None = Field(default=None, description="Sender email")
    to_emails: list[str] = Field(default_factory=list, description="Recipients")
    cc_emails: list[str] = Field(default_factory=list, description="CC recipients")
    bcc_emails: list[str] = Field(default_factory=list, description="BCC recipients")


class PylonSlackInfoForMessages(BaseModel):
    """Slack-specific information for messages.

    Attributes:
        channel_id: Slack channel ID.
        thread_ts: Slack thread timestamp.
        message_ts: Slack message timestamp.
    """

    model_config = ConfigDict(extra="ignore")

    channel_id: str | None = Field(default=None, description="Slack channel ID")
    thread_ts: str | None = Field(default=None, description="Thread timestamp")
    message_ts: str | None = Field(default=None, description="Message timestamp")


class PylonMessage(BaseModel):
    """Pylon message/comment entity.

    Attributes:
        id: Unique message identifier.
        message_html: HTML content of the message.
        message_text: Plain text content (if available).
        timestamp: When the message was created.
        source: Source channel: 'email', 'slack', 'chat', 'web', etc.
        author: Author information.
        is_private: Whether this is an internal/private message.
        email_info: Email-specific information.
        slack_info: Slack-specific information.
        attachments: List of attachments.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique message identifier")
    message_html: str | None = Field(default=None, description="HTML content")
    message_text: str | None = Field(default=None, description="Plain text content")
    timestamp: datetime = Field(description="When the message was created")
    source: str | None = Field(default=None, description="Source channel")
    author: PylonMessageAuthor | None = Field(default=None, description="Author info")
    is_private: bool = Field(default=False, description="Is internal/private message")
    email_info: PylonEmailInfo | None = Field(default=None, description="Email info")
    slack_info: PylonSlackInfoForMessages | None = Field(
        default=None,
        description="Slack info",
    )
    attachments: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Attachments",
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonMessage:
        """Create a PylonMessage from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonMessage instance.
        """
        # Make a copy to avoid mutating input
        parsed_data = data.copy()

        # Parse file_urls into attachments
        if "file_urls" in parsed_data and parsed_data["file_urls"]:
            attachments = []
            uuid_pattern = (
                r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}-(.+)$"
            )
            for url in parsed_data["file_urls"]:
                parsed_url = urlparse(url)
                decoded_path = unquote(parsed_url.path)
                filename = decoded_path.split("/")[-1]
                match = re.match(uuid_pattern, filename)
                if match:
                    filename = match.group(1)
                attachments.append({"url": url, "filename": filename})
            parsed_data["attachments"] = attachments
            del parsed_data["file_urls"]

        return cls.model_validate(parsed_data)
