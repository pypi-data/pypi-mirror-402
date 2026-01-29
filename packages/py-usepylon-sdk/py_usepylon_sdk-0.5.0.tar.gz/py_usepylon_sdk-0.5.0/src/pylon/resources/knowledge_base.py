"""Knowledge Base resource for the Pylon SDK.

This module provides resource classes for interacting with the
Pylon Knowledge Base API endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

from pylon.models.knowledge_base import PylonKnowledgeBase, PylonKnowledgeBaseArticle
from pylon.resources._base import BaseAsyncResource, BaseSyncResource
from pylon.resources._pagination import AsyncPaginator, SyncPaginator

if TYPE_CHECKING:
    from pylon._http import AsyncHTTPTransport, SyncHTTPTransport


class KnowledgeBaseResource(BaseSyncResource[PylonKnowledgeBase]):
    """Synchronous resource for managing Pylon knowledge bases.

    Provides methods for listing, retrieving knowledge bases and articles.
    """

    _endpoint = "/knowledge-bases"
    _model = PylonKnowledgeBase

    def __init__(self, transport: SyncHTTPTransport) -> None:
        """Initialize the knowledge base resource."""
        super().__init__(transport)

    def list(self, *, limit: int = 100) -> Iterator[PylonKnowledgeBase]:
        """List all knowledge bases.

        Args:
            limit: Number of items per page.

        Yields:
            PylonKnowledgeBase instances.
        """
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonKnowledgeBase.from_pylon_dict,
        )
        yield from paginator.iter()

    def get(self, kb_id: str) -> PylonKnowledgeBase:
        """Get a specific knowledge base by ID.

        Args:
            kb_id: The knowledge base ID.

        Returns:
            The PylonKnowledgeBase instance.
        """
        response = self._get(f"{self._endpoint}/{kb_id}")
        data = response.get("data", response)
        return PylonKnowledgeBase.from_pylon_dict(data)

    def list_articles(
        self, kb_id: str, *, limit: int = 100
    ) -> Iterator[PylonKnowledgeBaseArticle]:
        """List articles in a knowledge base.

        Args:
            kb_id: The knowledge base ID.
            limit: Number of items per page.

        Yields:
            PylonKnowledgeBaseArticle instances.
        """
        paginator = SyncPaginator(
            transport=self._transport,
            endpoint=f"{self._endpoint}/{kb_id}/articles",
            model=PylonKnowledgeBaseArticle,
            params={"limit": limit},
            parser=PylonKnowledgeBaseArticle.from_pylon_dict,
        )
        yield from paginator.iter()

    def get_article(self, kb_id: str, article_id: str) -> PylonKnowledgeBaseArticle:
        """Get a specific article by ID.

        Args:
            kb_id: The knowledge base ID.
            article_id: The article ID.

        Returns:
            The PylonKnowledgeBaseArticle instance.
        """
        response = self._get(f"{self._endpoint}/{kb_id}/articles/{article_id}")
        data = response.get("data", response)
        return PylonKnowledgeBaseArticle.from_pylon_dict(data)

    def create_article(
        self,
        kb_id: str,
        *,
        title: str,
        content: str,
        status: str = "draft",
        **kwargs: Any,
    ) -> PylonKnowledgeBaseArticle:
        """Create a new article in a knowledge base.

        Args:
            kb_id: The knowledge base ID.
            title: Article title.
            content: Article content (HTML or Markdown).
            status: Article status (default: "draft").
            **kwargs: Additional fields.

        Returns:
            The created PylonKnowledgeBaseArticle instance.
        """
        data = {"title": title, "content": content, "status": status, **kwargs}
        response = self._post(f"{self._endpoint}/{kb_id}/articles", data=data)
        result = response.get("data", response)
        return PylonKnowledgeBaseArticle.from_pylon_dict(result)


class AsyncKnowledgeBaseResource(BaseAsyncResource[PylonKnowledgeBase]):
    """Asynchronous resource for managing Pylon knowledge bases.

    Provides async methods for listing, retrieving knowledge bases and articles.
    """

    _endpoint = "/knowledge-bases"
    _model = PylonKnowledgeBase

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        """Initialize the async knowledge base resource."""
        super().__init__(transport)

    async def list(self, *, limit: int = 100) -> AsyncIterator[PylonKnowledgeBase]:
        """List all knowledge bases asynchronously.

        Args:
            limit: Number of items per page.

        Yields:
            PylonKnowledgeBase instances.
        """
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=self._endpoint,
            model=self._model,
            params={"limit": limit},
            parser=PylonKnowledgeBase.from_pylon_dict,
        )
        async for kb in paginator:
            yield kb

    async def get(self, kb_id: str) -> PylonKnowledgeBase:
        """Get a specific knowledge base by ID asynchronously."""
        response = await self._get(f"{self._endpoint}/{kb_id}")
        data = response.get("data", response)
        return PylonKnowledgeBase.from_pylon_dict(data)

    async def list_articles(
        self, kb_id: str, *, limit: int = 100
    ) -> AsyncIterator[PylonKnowledgeBaseArticle]:
        """List articles in a knowledge base asynchronously.

        Args:
            kb_id: The knowledge base ID.
            limit: Number of items per page.

        Yields:
            PylonKnowledgeBaseArticle instances.
        """
        paginator = AsyncPaginator(
            transport=self._transport,
            endpoint=f"{self._endpoint}/{kb_id}/articles",
            model=PylonKnowledgeBaseArticle,
            params={"limit": limit},
            parser=PylonKnowledgeBaseArticle.from_pylon_dict,
        )
        async for article in paginator:
            yield article

    async def get_article(
        self, kb_id: str, article_id: str
    ) -> PylonKnowledgeBaseArticle:
        """Get a specific article by ID asynchronously.

        Args:
            kb_id: The knowledge base ID.
            article_id: The article ID.

        Returns:
            The PylonKnowledgeBaseArticle instance.
        """
        response = await self._get(f"{self._endpoint}/{kb_id}/articles/{article_id}")
        data = response.get("data", response)
        return PylonKnowledgeBaseArticle.from_pylon_dict(data)

    async def create_article(
        self,
        kb_id: str,
        *,
        title: str,
        content: str,
        status: str = "draft",
        **kwargs: Any,
    ) -> PylonKnowledgeBaseArticle:
        """Create a new article in a knowledge base asynchronously.

        Args:
            kb_id: The knowledge base ID.
            title: Article title.
            content: Article content (HTML or Markdown).
            status: Article status (default: "draft").
            **kwargs: Additional fields.

        Returns:
            The created PylonKnowledgeBaseArticle instance.
        """
        data = {"title": title, "content": content, "status": status, **kwargs}
        response = await self._post(f"{self._endpoint}/{kb_id}/articles", data=data)
        result = response.get("data", response)
        return PylonKnowledgeBaseArticle.from_pylon_dict(result)
