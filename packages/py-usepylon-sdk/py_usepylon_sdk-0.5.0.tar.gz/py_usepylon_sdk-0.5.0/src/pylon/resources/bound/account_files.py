"""Bound resource for account files."""

from __future__ import annotations

from pylon.models.files import PylonFile
from pylon.resources._bound import BoundAsyncResource, BoundSyncResource


class AccountFilesSyncResource(BoundSyncResource[PylonFile]):
    """Synchronous resource for account files.

    Provides access to files associated with a specific account.

    Example:
        account = client.accounts.get("acc_123")
        for file in account.files.list():
            print(f"{file.filename}: {file.url}")
    """

    _parent_path = "accounts"
    _resource_name = "files"
    _model = PylonFile
    _parser = PylonFile.from_pylon_dict


class AccountFilesAsyncResource(BoundAsyncResource[PylonFile]):
    """Asynchronous resource for account files.

    Provides async access to files associated with a specific account.

    Example:
        account = await client.accounts.get("acc_123")
        async for file in account.files.list():
            print(f"{file.filename}: {file.url}")
    """

    _parent_path = "accounts"
    _resource_name = "files"
    _model = PylonFile
    _parser = PylonFile.from_pylon_dict
