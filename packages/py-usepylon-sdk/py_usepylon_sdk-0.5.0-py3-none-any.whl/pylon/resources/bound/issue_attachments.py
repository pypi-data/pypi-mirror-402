"""Bound resource for issue attachments."""

from __future__ import annotations

from typing import Any

from pylon.models.attachments import PylonAttachment
from pylon.resources._bound import BoundAsyncResource, BoundSyncResource


class IssueAttachmentsSyncResource(BoundSyncResource[PylonAttachment]):
    """Synchronous resource for issue attachments.

    Provides access to attachments associated with a specific issue.

    Example:
        issue = client.issues.get("issue_123")
        for attachment in issue.attachments.list():
            print(f"{attachment.filename}: {attachment.url}")
    """

    _parent_path = "issues"
    _resource_name = "attachments"
    _model = PylonAttachment
    _parser = PylonAttachment.from_pylon_dict

    def create(  # type: ignore[override]
        self,
        *,
        filename: str,
        url: str,
        content_type: str | None = None,
        **kwargs: Any,
    ) -> PylonAttachment:
        """Create a new attachment on this issue.

        Args:
            filename: Name of the file.
            url: URL to the file.
            content_type: MIME type of the file.
            **kwargs: Additional fields.

        Returns:
            The created PylonAttachment instance.
        """
        data: dict[str, Any] = {"filename": filename, "url": url, **kwargs}
        if content_type:
            data["content_type"] = content_type
        response = self._post(self._base_path, data=data)
        return self._parse_single(response)


class IssueAttachmentsAsyncResource(BoundAsyncResource[PylonAttachment]):
    """Asynchronous resource for issue attachments.

    Provides async access to attachments associated with a specific issue.

    Example:
        issue = await client.issues.get("issue_123")
        async for attachment in issue.attachments.list():
            print(f"{attachment.filename}: {attachment.url}")
    """

    _parent_path = "issues"
    _resource_name = "attachments"
    _model = PylonAttachment
    _parser = PylonAttachment.from_pylon_dict

    async def create(  # type: ignore[override]
        self,
        *,
        filename: str,
        url: str,
        content_type: str | None = None,
        **kwargs: Any,
    ) -> PylonAttachment:
        """Create a new attachment on this issue asynchronously.

        Args:
            filename: Name of the file.
            url: URL to the file.
            content_type: MIME type of the file.
            **kwargs: Additional fields.

        Returns:
            The created PylonAttachment instance.
        """
        data: dict[str, Any] = {"filename": filename, "url": url, **kwargs}
        if content_type:
            data["content_type"] = content_type
        response = await self._post(self._base_path, data=data)
        return self._parse_single(response)
