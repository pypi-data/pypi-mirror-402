"""Bound resource for account highlights."""

from __future__ import annotations

from pylon.models.highlights import PylonHighlight
from pylon.resources._bound import BoundAsyncResource, BoundSyncResource


class AccountHighlightsSyncResource(BoundSyncResource[PylonHighlight]):
    """Synchronous resource for account highlights.

    Provides access to highlights/notes associated with a specific account.

    Example:
        account = client.accounts.get("acc_123")
        for highlight in account.highlights.list():
            print(f"{highlight.title}: {highlight.content}")
    """

    _parent_path = "accounts"
    _resource_name = "highlights"
    _model = PylonHighlight
    _parser = PylonHighlight.from_pylon_dict


class AccountHighlightsAsyncResource(BoundAsyncResource[PylonHighlight]):
    """Asynchronous resource for account highlights.

    Provides async access to highlights/notes associated with a specific account.

    Example:
        account = await client.accounts.get("acc_123")
        async for highlight in account.highlights.list():
            print(f"{highlight.title}: {highlight.content}")
    """

    _parent_path = "accounts"
    _resource_name = "highlights"
    _model = PylonHighlight
    _parser = PylonHighlight.from_pylon_dict
