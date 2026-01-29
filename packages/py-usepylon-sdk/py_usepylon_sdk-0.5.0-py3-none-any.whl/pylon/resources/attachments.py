"""Attachments resource for the Pylon SDK.

This module provides resource classes for interacting with the
Pylon Attachments API endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

from pylon.models import PylonAttachment
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class AttachmentsResource(BaseSyncResource[PylonAttachment]):
    """Synchronous resource for managing Pylon attachments.

    Provides methods for listing, retrieving, and creating attachments
    via the Pylon API.
    """

    _endpoint = "/attachments"
    _model = PylonAttachment

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the attachments resource."""
        super().__init__(transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonAttachment]:
        """List all attachments.

        Args:
            limit: Number of items per page.

        Yields:
            PylonAttachment instances.
        """
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonAttachment.from_pylon_dict,
        )
        yield from paginator.iter()

    def get(self, attachment_id: str) -> PylonAttachment:
        """Get a specific attachment by ID.

        Args:
            attachment_id: The attachment ID.

        Returns:
            The PylonAttachment instance.
        """
        response = self._get(f"{self._endpoint}/{attachment_id}")
        data = response.get("data", response)
        return PylonAttachment.from_pylon_dict(data)

    def create(
        self,
        *,
        filename: str,
        content_type: str,
        content: bytes,
        **kwargs: Any,
    ) -> PylonAttachment:
        """Create a new attachment.

        Args:
            filename: Name of the file.
            content_type: MIME type of the file.
            content: File content as bytes.
            **kwargs: Additional fields.

        Returns:
            The created PylonAttachment instance.
        """
        import base64

        data = {
            "filename": filename,
            "content_type": content_type,
            "content": base64.b64encode(content).decode("utf-8"),
            **kwargs,
        }
        response = self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonAttachment.from_pylon_dict(result)

    def create_from_url(
        self,
        *,
        file_url: str,
        description: str | None = None,
        **kwargs: Any,
    ) -> PylonAttachment:
        """Create an attachment from a URL.

        Downloads the file from the URL and creates an attachment.

        Args:
            file_url: URL of the file to download.
            description: Optional description.
            **kwargs: Additional fields.

        Returns:
            The created PylonAttachment instance.
        """
        data: dict[str, Any] = {"file_url": file_url, **kwargs}
        if description:
            data["description"] = description
        response = self._post(f"{self._endpoint}/from-url", data=data)
        result = response.get("data", response)
        return PylonAttachment.from_pylon_dict(result)


class AsyncAttachmentsResource(BaseAsyncResource[PylonAttachment]):
    """Asynchronous resource for managing Pylon attachments.

    Provides async methods for listing, retrieving, and creating attachments
    via the Pylon API.
    """

    _endpoint = "/attachments"
    _model = PylonAttachment

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the async attachments resource."""
        super().__init__(transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonAttachment]:
        """List all attachments asynchronously.

        Args:
            limit: Number of items per page.

        Yields:
            PylonAttachment instances.
        """
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonAttachment.from_pylon_dict,
        )
        async for attachment in paginator:
            yield attachment

    async def get(self, attachment_id: str) -> PylonAttachment:
        """Get a specific attachment by ID asynchronously.

        Args:
            attachment_id: The attachment ID.

        Returns:
            The PylonAttachment instance.
        """
        response = await self._get(f"{self._endpoint}/{attachment_id}")
        data = response.get("data", response)
        return PylonAttachment.from_pylon_dict(data)

    async def create(
        self,
        *,
        filename: str,
        content_type: str,
        content: bytes,
        **kwargs: Any,
    ) -> PylonAttachment:
        """Create a new attachment asynchronously.

        Args:
            filename: Name of the file.
            content_type: MIME type of the file.
            content: File content as bytes.
            **kwargs: Additional fields.

        Returns:
            The created PylonAttachment instance.
        """
        import base64

        data = {
            "filename": filename,
            "content_type": content_type,
            "content": base64.b64encode(content).decode("utf-8"),
            **kwargs,
        }
        response = await self._post(self._endpoint, data=data)
        result = response.get("data", response)
        return PylonAttachment.from_pylon_dict(result)

    async def create_from_url(
        self,
        *,
        file_url: str,
        description: str | None = None,
        **kwargs: Any,
    ) -> PylonAttachment:
        """Create an attachment from a URL asynchronously.

        Downloads the file from the URL and creates an attachment.

        Args:
            file_url: URL of the file to download.
            description: Optional description.
            **kwargs: Additional fields.

        Returns:
            The created PylonAttachment instance.
        """
        data: dict[str, Any] = {"file_url": file_url, **kwargs}
        if description:
            data["description"] = description
        response = await self._post(f"{self._endpoint}/from-url", data=data)
        result = response.get("data", response)
        return PylonAttachment.from_pylon_dict(result)
