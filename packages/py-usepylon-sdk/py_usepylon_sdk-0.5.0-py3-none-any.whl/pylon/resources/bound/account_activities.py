"""Bound resource for account activities."""

from __future__ import annotations

from pylon.models.activities import PylonActivity
from pylon.resources._bound import BoundAsyncResource, BoundSyncResource


class AccountActivitiesSyncResource(BoundSyncResource[PylonActivity]):
    """Synchronous resource for account activities.

    Provides access to activities associated with a specific account.

    Example:
        account = client.accounts.get("acc_123")
        for activity in account.activities.list():
            print(f"{activity.type}: {activity.description}")
    """

    _parent_path = "accounts"
    _resource_name = "activities"
    _model = PylonActivity
    _parser = PylonActivity.from_pylon_dict


class AccountActivitiesAsyncResource(BoundAsyncResource[PylonActivity]):
    """Asynchronous resource for account activities.

    Provides async access to activities associated with a specific account.

    Example:
        account = await client.accounts.get("acc_123")
        async for activity in account.activities.list():
            print(f"{activity.type}: {activity.description}")
    """

    _parent_path = "accounts"
    _resource_name = "activities"
    _model = PylonActivity
    _parser = PylonActivity.from_pylon_dict
