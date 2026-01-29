"""Base models shared across Pylon API entities.

This module contains foundational models that are used by multiple
other models throughout the SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from pylon.exceptions import PylonError

if TYPE_CHECKING:
    from pylon._client import AsyncPylonClient, PylonClient

# TypeVar for self-returning methods
T = TypeVar("T", bound="RichModelMixin")


class ClientNotBoundError(PylonError):
    """Raised when a rich method is called on a model without a bound client.

    This error occurs when trying to use methods like `issue.resolve()` or
    `account.refresh()` on a model that was not retrieved through the client
    or was manually constructed.
    """

    def __init__(self, model_name: str, method_name: str) -> None:
        """Initialize the error.

        Args:
            model_name: Name of the model class (e.g., "PylonIssue").
            method_name: Name of the method that was called.
        """
        self.model_name = model_name
        self.method_name = method_name
        super().__init__(
            f"Cannot call {method_name}() on {model_name}: "
            "model is not bound to a client. "
            "Retrieve the model using the appropriate client resource method "
            "(e.g., client.issues.get(), client.accounts.get())."
        )


class RichModelMixin:
    """Mixin class providing client binding for rich model methods.

    This mixin adds the ability for Pydantic models to store a reference
    to the client that created them, enabling rich methods like
    `issue.resolve()` or `account.refresh()`.

    The mixin handles both sync and async clients and provides helper
    methods for checking and ensuring client availability.
    """

    # Private attributes for client reference
    _sync_client: PylonClient | None = PrivateAttr(default=None)
    _async_client: AsyncPylonClient | None = PrivateAttr(default=None)

    def _bind_client(self: T, client: PylonClient | AsyncPylonClient) -> T:
        """Bind a client to this model for rich method support.

        Args:
            client: The Pylon client (sync or async) to bind.

        Returns:
            Self for method chaining.
        """
        # Import here to avoid circular imports
        from pylon._client import AsyncPylonClient, PylonClient

        if isinstance(client, PylonClient):
            self._sync_client = client
            self._async_client = None  # Clear async to avoid context mismatch
        elif isinstance(client, AsyncPylonClient):
            self._async_client = client
            self._sync_client = None  # Clear sync to avoid context mismatch
        return self

    def _ensure_client(self, method_name: str) -> None:
        """Ensure a client is bound to this model.

        Args:
            method_name: Name of the method requiring the client.

        Raises:
            ClientNotBoundError: If no client is bound.
        """
        if self._sync_client is None and self._async_client is None:
            raise ClientNotBoundError(self.__class__.__name__, method_name)

    @property
    def _has_sync_client(self) -> bool:
        """Check if a sync client is bound."""
        return self._sync_client is not None

    @property
    def _has_async_client(self) -> bool:
        """Check if an async client is bound."""
        return self._async_client is not None

    def _update_from(self: T, other: T) -> None:
        """Update this model's fields from another instance.

        This method copies all public field values from `other` to `self`,
        allowing in-place updates after API calls.

        Args:
            other: Another instance of the same model type.
        """
        # Get model fields from the class (not instance) per Pydantic v2.11+
        if hasattr(self.__class__, "model_fields"):
            for field_name in self.__class__.model_fields:  # type: ignore[attr-defined]
                setattr(self, field_name, getattr(other, field_name))

    def _copy_client_binding(self: T, other: RichModelMixin) -> T:
        """Copy client binding from another model.

        Args:
            other: Model to copy binding from.

        Returns:
            Self for method chaining.
        """
        self._sync_client = other._sync_client
        self._async_client = other._async_client
        return self


class PylonReference(BaseModel):
    """Reference to another Pylon entity (just ID).

    Many Pylon API responses include references to related entities
    as simple objects containing just an ID. This model represents
    those references.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
    )

    id: str = Field(description="The ID of the referenced entity")


class PylonCustomFieldValue(BaseModel):
    """Custom field value structure used by Pylon.

    In API responses, `custom_fields` are represented as an object keyed by
    slug, where each value includes at least a `value` and, for multi-select
    fields, `values`. Some APIs also repeat the slug inside the value
    payload, so we capture that here when present.

    Attributes:
        slug: The custom field slug (optional, may be included in payload).
        value: The primary value of the custom field.
        values: For multi-select fields, a list of selected values.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    slug: str | None = Field(default=None, description="The custom field slug")
    value: str = Field(default="", description="The custom field value")
    values: list[str] | None = Field(
        default=None,
        description="For multi-select fields, the list of selected values",
    )
