"""Pylon API Client implementations.

This module provides the main client classes for interacting with
the Pylon API using both synchronous and asynchronous patterns.
"""

from __future__ import annotations

import os
from typing import Any

from pylon._http import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    AsyncHTTPTransport,
    SyncHTTPTransport,
)
from pylon.resources.accounts import AccountsResource, AsyncAccountsResource
from pylon.resources.attachments import (
    AsyncAttachmentsResource,
    AttachmentsResource,
)
from pylon.resources.audit_logs import AsyncAuditLogsResource, AuditLogsResource
from pylon.resources.contacts import AsyncContactsResource, ContactsResource
from pylon.resources.custom_fields import (
    AsyncCustomFieldsResource,
    CustomFieldsResource,
)
from pylon.resources.issues import AsyncIssuesResource, IssuesResource
from pylon.resources.knowledge_base import (
    AsyncKnowledgeBaseResource,
    KnowledgeBaseResource,
)
from pylon.resources.me import AsyncMeResource, MeResource
from pylon.resources.messages import AsyncMessagesResource, MessagesResource
from pylon.resources.projects import AsyncProjectsResource, ProjectsResource
from pylon.resources.tags import AsyncTagsResource, TagsResource
from pylon.resources.tasks import AsyncTasksResource, TasksResource
from pylon.resources.teams import AsyncTeamsResource, TeamsResource
from pylon.resources.ticket_forms import AsyncTicketFormsResource, TicketFormsResource
from pylon.resources.user_roles import AsyncUserRolesResource, UserRolesResource
from pylon.resources.users import AsyncUsersResource, UsersResource


class PylonClient:
    """Synchronous client for the Pylon API.

    Provides a resource-based interface for interacting with the Pylon
    customer support API. Uses httpx for HTTP requests with connection
    pooling and automatic retries.

    Example:
        # Basic usage
        client = PylonClient(api_key="...")

        # List recent issues
        for issue in client.issues.list(days=7):
            print(f"#{issue.number}: {issue.title}")

        # Get a specific issue
        issue = client.issues.get("issue_123")

        # Context manager usage (recommended)
        with PylonClient(api_key="...") as client:
            for account in client.accounts.list():
                print(account.name)

    Attributes:
        issues: Resource for managing issues.
        accounts: Resource for managing accounts.
        attachments: Resource for managing attachments.
        audit_logs: Resource for accessing audit logs.
        contacts: Resource for managing contacts.
        custom_fields: Resource for managing custom field definitions.
        knowledge_bases: Resource for managing knowledge bases.
        me: Resource for accessing current user info.
        messages: Resource for managing issue messages.
        projects: Resource for managing projects.
        tags: Resource for managing tags.
        tasks: Resource for managing tasks.
        teams: Resource for managing teams.
        ticket_forms: Resource for accessing ticket form definitions.
        user_roles: Resource for accessing user role definitions.
        users: Resource for managing users.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """Initialize the Pylon client.

        Args:
            api_key: Pylon API key. If not provided, uses PYLON_API_KEY env var.
            base_url: Base URL for the Pylon API.
            timeout: Timeout in seconds for HTTP requests.
            max_retries: Maximum number of retry attempts for failed requests.

        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        resolved_api_key = api_key or os.getenv("PYLON_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "Pylon API key must be provided or set in PYLON_API_KEY environment "
                "variable."
            )

        self._transport = SyncHTTPTransport(
            api_key=resolved_api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Initialize resources (issues gets client reference for rich methods)
        self._issues = IssuesResource(self._transport, client=self)
        self._accounts = AccountsResource(self._transport)
        self._attachments = AttachmentsResource(self._transport)
        self._audit_logs = AuditLogsResource(self._transport)
        self._contacts = ContactsResource(self._transport)
        self._custom_fields = CustomFieldsResource(self._transport)
        self._knowledge_bases = KnowledgeBaseResource(self._transport)
        self._me = MeResource(self._transport)
        self._messages = MessagesResource(self._transport)
        self._projects = ProjectsResource(self._transport)
        self._tags = TagsResource(self._transport)
        self._tasks = TasksResource(self._transport)
        self._teams = TeamsResource(self._transport)
        self._ticket_forms = TicketFormsResource(self._transport)
        self._user_roles = UserRolesResource(self._transport)
        self._users = UsersResource(self._transport)

    @property
    def issues(self) -> IssuesResource:
        """Access the issues resource."""
        return self._issues

    @property
    def accounts(self) -> AccountsResource:
        """Access the accounts resource."""
        return self._accounts

    @property
    def attachments(self) -> AttachmentsResource:
        """Access the attachments resource."""
        return self._attachments

    @property
    def audit_logs(self) -> AuditLogsResource:
        """Access the audit logs resource."""
        return self._audit_logs

    @property
    def contacts(self) -> ContactsResource:
        """Access the contacts resource."""
        return self._contacts

    @property
    def custom_fields(self) -> CustomFieldsResource:
        """Access the custom fields resource."""
        return self._custom_fields

    @property
    def knowledge_bases(self) -> KnowledgeBaseResource:
        """Access the knowledge bases resource."""
        return self._knowledge_bases

    @property
    def me(self) -> MeResource:
        """Access the current user (me) resource."""
        return self._me

    @property
    def messages(self) -> MessagesResource:
        """Access the messages resource."""
        return self._messages

    @property
    def projects(self) -> ProjectsResource:
        """Access the projects resource."""
        return self._projects

    @property
    def tags(self) -> TagsResource:
        """Access the tags resource."""
        return self._tags

    @property
    def tasks(self) -> TasksResource:
        """Access the tasks resource."""
        return self._tasks

    @property
    def teams(self) -> TeamsResource:
        """Access the teams resource."""
        return self._teams

    @property
    def ticket_forms(self) -> TicketFormsResource:
        """Access the ticket forms resource."""
        return self._ticket_forms

    @property
    def user_roles(self) -> UserRolesResource:
        """Access the user roles resource."""
        return self._user_roles

    @property
    def users(self) -> UsersResource:
        """Access the users resource."""
        return self._users

    def close(self) -> None:
        """Close the client and release resources."""
        self._transport.close()

    def __enter__(self) -> PylonClient:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit."""
        self.close()


class AsyncPylonClient:
    """Asynchronous client for the Pylon API.

    Provides a resource-based interface for interacting with the Pylon
    customer support API using async/await. Uses httpx.AsyncClient for
    efficient asynchronous HTTP requests.

    Example:
        # Basic usage with async context manager
        async with AsyncPylonClient(api_key="...") as client:
            # List recent issues
            async for issue in client.issues.list(days=7):
                print(f"#{issue.number}: {issue.title}")

            # Get a specific issue
            issue = await client.issues.get("issue_123")

    Attributes:
        issues: Async resource for managing issues.
        accounts: Async resource for managing accounts.
        attachments: Async resource for managing attachments.
        audit_logs: Async resource for accessing audit logs.
        contacts: Async resource for managing contacts.
        custom_fields: Async resource for managing custom field definitions.
        knowledge_bases: Async resource for managing knowledge bases.
        me: Async resource for accessing current user info.
        messages: Async resource for managing issue messages.
        projects: Async resource for managing projects.
        tags: Async resource for managing tags.
        tasks: Async resource for managing tasks.
        teams: Async resource for managing teams.
        ticket_forms: Async resource for accessing ticket form definitions.
        user_roles: Async resource for accessing user role definitions.
        users: Async resource for managing users.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """Initialize the async Pylon client.

        Args:
            api_key: Pylon API key. If not provided, uses PYLON_API_KEY env var.
            base_url: Base URL for the Pylon API.
            timeout: Timeout in seconds for HTTP requests.
            max_retries: Maximum number of retry attempts for failed requests.

        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        resolved_api_key = api_key or os.getenv("PYLON_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "Pylon API key must be provided or set in PYLON_API_KEY environment "
                "variable."
            )

        self._transport = AsyncHTTPTransport(
            api_key=resolved_api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Initialize async resources (issues gets client reference for rich methods)
        self._issues = AsyncIssuesResource(self._transport, client=self)
        self._accounts = AsyncAccountsResource(self._transport)
        self._attachments = AsyncAttachmentsResource(self._transport)
        self._audit_logs = AsyncAuditLogsResource(self._transport)
        self._contacts = AsyncContactsResource(self._transport)
        self._custom_fields = AsyncCustomFieldsResource(self._transport)
        self._knowledge_bases = AsyncKnowledgeBaseResource(self._transport)
        self._me = AsyncMeResource(self._transport)
        self._messages = AsyncMessagesResource(self._transport)
        self._projects = AsyncProjectsResource(self._transport)
        self._tags = AsyncTagsResource(self._transport)
        self._tasks = AsyncTasksResource(self._transport)
        self._teams = AsyncTeamsResource(self._transport)
        self._ticket_forms = AsyncTicketFormsResource(self._transport)
        self._user_roles = AsyncUserRolesResource(self._transport)
        self._users = AsyncUsersResource(self._transport)

    @property
    def issues(self) -> AsyncIssuesResource:
        """Access the async issues resource."""
        return self._issues

    @property
    def accounts(self) -> AsyncAccountsResource:
        """Access the async accounts resource."""
        return self._accounts

    @property
    def attachments(self) -> AsyncAttachmentsResource:
        """Access the async attachments resource."""
        return self._attachments

    @property
    def audit_logs(self) -> AsyncAuditLogsResource:
        """Access the async audit logs resource."""
        return self._audit_logs

    @property
    def contacts(self) -> AsyncContactsResource:
        """Access the async contacts resource."""
        return self._contacts

    @property
    def custom_fields(self) -> AsyncCustomFieldsResource:
        """Access the async custom fields resource."""
        return self._custom_fields

    @property
    def knowledge_bases(self) -> AsyncKnowledgeBaseResource:
        """Access the async knowledge bases resource."""
        return self._knowledge_bases

    @property
    def me(self) -> AsyncMeResource:
        """Access the async current user (me) resource."""
        return self._me

    @property
    def messages(self) -> AsyncMessagesResource:
        """Access the async messages resource."""
        return self._messages

    @property
    def projects(self) -> AsyncProjectsResource:
        """Access the async projects resource."""
        return self._projects

    @property
    def tags(self) -> AsyncTagsResource:
        """Access the async tags resource."""
        return self._tags

    @property
    def tasks(self) -> AsyncTasksResource:
        """Access the async tasks resource."""
        return self._tasks

    @property
    def teams(self) -> AsyncTeamsResource:
        """Access the async teams resource."""
        return self._teams

    @property
    def ticket_forms(self) -> AsyncTicketFormsResource:
        """Access the async ticket forms resource."""
        return self._ticket_forms

    @property
    def user_roles(self) -> AsyncUserRolesResource:
        """Access the async user roles resource."""
        return self._user_roles

    @property
    def users(self) -> AsyncUsersResource:
        """Access the async users resource."""
        return self._users

    async def aclose(self) -> None:
        """Close the async client and release resources."""
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncPylonClient:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.aclose()
