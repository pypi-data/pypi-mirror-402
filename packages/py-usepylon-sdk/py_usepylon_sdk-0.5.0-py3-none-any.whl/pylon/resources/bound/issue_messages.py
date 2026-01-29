"""Bound resource for issue messages."""

from __future__ import annotations

from typing import Any

from pylon.models.messages import PylonMessage
from pylon.resources._bound import BoundAsyncResource, BoundSyncResource


class IssueMessagesSyncResource(BoundSyncResource[PylonMessage]):
    """Synchronous resource for issue messages.

    Provides access to messages associated with a specific issue.

    Example:
        issue = client.issues.get("issue_123")
        for message in issue.messages.list():
            print(f"{message.author}: {message.message_text}")
    """

    _parent_path = "issues"
    _resource_name = "messages"
    _model = PylonMessage
    _parser = PylonMessage.from_pylon_dict

    def create(  # type: ignore[override]
        self,
        *,
        content: str,
        is_private: bool = False,
        **kwargs: Any,
    ) -> PylonMessage:
        """Create a new message on this issue.

        Args:
            content: The message content.
            is_private: Whether this is an internal/private message.
            **kwargs: Additional fields.

        Returns:
            The created PylonMessage instance.
        """
        data = {"content": content, "is_private": is_private, **kwargs}
        response = self._post(self._base_path, data=data)
        return self._parse_single(response)


class IssueMessagesAsyncResource(BoundAsyncResource[PylonMessage]):
    """Asynchronous resource for issue messages.

    Provides async access to messages associated with a specific issue.

    Example:
        issue = await client.issues.get("issue_123")
        async for message in issue.messages.list():
            print(f"{message.author}: {message.message_text}")
    """

    _parent_path = "issues"
    _resource_name = "messages"
    _model = PylonMessage
    _parser = PylonMessage.from_pylon_dict

    async def create(  # type: ignore[override]
        self,
        *,
        content: str,
        is_private: bool = False,
        **kwargs: Any,
    ) -> PylonMessage:
        """Create a new message on this issue asynchronously.

        Args:
            content: The message content.
            is_private: Whether this is an internal/private message.
            **kwargs: Additional fields.

        Returns:
            The created PylonMessage instance.
        """
        data = {"content": content, "is_private": is_private, **kwargs}
        response = await self._post(self._base_path, data=data)
        return self._parse_single(response)
