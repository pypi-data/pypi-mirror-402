"""Pydantic models for Pylon knowledge base entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PylonKnowledgeBase(BaseModel):
    """Pylon knowledge base entity.

    Represents a knowledge base collection in Pylon.

    Attributes:
        id: Unique identifier for the knowledge base.
        name: Name of the knowledge base.
        description: Description of the knowledge base.
        article_count: Number of articles in the knowledge base.
        created_at: When the knowledge base was created.
        updated_at: When the knowledge base was last updated.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier for the knowledge base")
    name: str = Field(description="Name of the knowledge base")
    description: str | None = Field(
        default=None, description="Description of the knowledge base"
    )
    article_count: int = Field(default=0, description="Number of articles")
    created_at: datetime | None = Field(
        default=None, description="When the knowledge base was created"
    )
    updated_at: datetime | None = Field(
        default=None, description="When the knowledge base was last updated"
    )

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonKnowledgeBase:
        """Create a PylonKnowledgeBase from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonKnowledgeBase instance.
        """
        return cls.model_validate(data)


class PylonKnowledgeBaseArticle(BaseModel):
    """Pylon knowledge base article entity.

    Represents an article in a Pylon knowledge base.

    Attributes:
        id: Unique identifier for the article.
        title: Article title.
        content: Article content (HTML or Markdown).
        knowledge_base_id: ID of the parent knowledge base.
        status: Article status (draft, published, archived).
        created_at: When the article was created.
        updated_at: When the article was last updated.
        author_id: ID of the article author.
        view_count: Number of views.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier for the article")
    title: str = Field(description="Article title")
    content: str | None = Field(default=None, description="Article content")
    knowledge_base_id: str = Field(description="ID of the parent knowledge base")
    status: str = Field(default="draft", description="Article status")
    created_at: datetime | None = Field(
        default=None, description="When the article was created"
    )
    updated_at: datetime | None = Field(
        default=None, description="When the article was last updated"
    )
    author_id: str | None = Field(default=None, description="ID of the author")
    view_count: int = Field(default=0, description="Number of views")

    @classmethod
    def from_pylon_dict(cls, data: dict[str, Any]) -> PylonKnowledgeBaseArticle:
        """Create a PylonKnowledgeBaseArticle from Pylon API response.

        Args:
            data: Raw dictionary from the Pylon API.

        Returns:
            A PylonKnowledgeBaseArticle instance.
        """
        return cls.model_validate(data)
