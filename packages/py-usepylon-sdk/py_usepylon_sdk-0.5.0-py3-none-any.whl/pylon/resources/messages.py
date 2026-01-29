"""Messages resource for the Pylon SDK.

This module provides resource classes for interacting with the
Pylon Messages API endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

from pylon.models import PylonMessage
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class MessagesResource(BaseSyncResource[PylonMessage]):
    """Synchronous resource for managing Pylon messages.

    Provides methods for listing, retrieving, and creating messages
    via the Pylon API.

    Example:
        client = PylonClient(api_key="...")

        # List messages for an issue
        for msg in client.messages.list(issue_id="issue_123"):
            print(f"{msg.author.name}: {msg.message_text}")

        # Create a new message
        msg = client.messages.create(
            issue_id="issue_123",
            content="Hello, how can I help?"
        )
    """

    _endpoint = "/issues"
    _model = PylonMessage

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the messages resource.

        Args:
            transport: The HTTP transport to use for requests.
        """
        super().__init__(transport)

    def list(
        self,
        issue_id: str,
        *,
        limit: int = 100,
    ) -> Iterator[PylonMessage]:
        """List messages for an issue.

        Args:
            issue_id: The issue ID to get messages for.
            limit: Maximum number of messages per page.

        Yields:
            PylonMessage instances.
        """
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=f"{self._endpoint}/{issue_id}/messages",
            model=self._model,
            params={"limit": limit},
            parser=PylonMessage.from_pylon_dict,
        )
        yield from paginator.iter()

    def get(self, issue_id: str, message_id: str) -> PylonMessage:
        """Get a specific message by ID.

        Args:
            issue_id: The issue ID.
            message_id: The message ID.

        Returns:
            The PylonMessage instance.
        """
        response = self._get(f"{self._endpoint}/{issue_id}/messages/{message_id}")
        data = response.get("data", response)
        return PylonMessage.from_pylon_dict(data)

    def create(
        self,
        issue_id: str,
        *,
        content: str,
        is_private: bool = False,
        **kwargs: Any,
    ) -> PylonMessage:
        """Create a new message on an issue.

        Args:
            issue_id: The issue ID to add the message to.
            content: The message content (HTML or text).
            is_private: Whether this is an internal/private message.
            **kwargs: Additional fields.

        Returns:
            The created PylonMessage instance.
        """
        data = {
            "content": content,
            "is_private": is_private,
            **kwargs,
        }
        response = self._post(f"{self._endpoint}/{issue_id}/messages", data=data)
        result = response.get("data", response)
        return PylonMessage.from_pylon_dict(result)


class AsyncMessagesResource(BaseAsyncResource[PylonMessage]):
    """Asynchronous resource for managing Pylon messages.

    Provides async methods for listing, retrieving, and creating messages
    via the Pylon API.

    Example:
        async with AsyncPylonClient(api_key="...") as client:
            # List messages for an issue
            async for msg in client.messages.list(issue_id="issue_123"):
                print(f"{msg.author.name}: {msg.message_text}")

            # Create a new message
            msg = await client.messages.create(
                issue_id="issue_123",
                content="Hello, how can I help?"
            )
    """

    _endpoint = "/issues"
    _model = PylonMessage

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the async messages resource.

        Args:
            transport: The async HTTP transport to use for requests.
        """
        super().__init__(transport)

    async def list(
        self,
        issue_id: str,
        *,
        limit: int = 100,
    ) -> AsyncIterator[PylonMessage]:
        """List messages for an issue asynchronously.

        Args:
            issue_id: The issue ID to get messages for.
            limit: Maximum number of messages per page.

        Yields:
            PylonMessage instances.
        """
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=f"{self._endpoint}/{issue_id}/messages",
            model=self._model,
            params={"limit": limit},
            parser=PylonMessage.from_pylon_dict,
        )
        async for message in paginator:
            yield message

    async def get(self, issue_id: str, message_id: str) -> PylonMessage:
        """Get a specific message by ID asynchronously.

        Args:
            issue_id: The issue ID.
            message_id: The message ID.

        Returns:
            The PylonMessage instance.
        """
        response = await self._get(f"{self._endpoint}/{issue_id}/messages/{message_id}")
        data = response.get("data", response)
        return PylonMessage.from_pylon_dict(data)

    async def create(
        self,
        issue_id: str,
        *,
        content: str,
        is_private: bool = False,
        **kwargs: Any,
    ) -> PylonMessage:
        """Create a new message on an issue asynchronously.

        Args:
            issue_id: The issue ID to add the message to.
            content: The message content (HTML or text).
            is_private: Whether this is an internal/private message.
            **kwargs: Additional fields.

        Returns:
            The created PylonMessage instance.
        """
        data = {
            "content": content,
            "is_private": is_private,
            **kwargs,
        }
        response = await self._post(f"{self._endpoint}/{issue_id}/messages", data=data)
        result = response.get("data", response)
        return PylonMessage.from_pylon_dict(result)
