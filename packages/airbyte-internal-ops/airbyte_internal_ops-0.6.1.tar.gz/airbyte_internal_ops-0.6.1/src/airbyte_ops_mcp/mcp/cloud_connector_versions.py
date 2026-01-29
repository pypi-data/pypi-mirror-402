# Copyright (c) 2025 Airbyte, Inc., all rights reserved.
"""MCP tools for cloud connector version management.

This module provides MCP tools for viewing and managing connector version
overrides (pins) in Airbyte Cloud. These tools enable admins to pin connectors
to specific versions for troubleshooting or stability purposes.

Uses direct API client calls with either bearer token or client credentials auth.
"""

# NOTE: We intentionally do NOT use `from __future__ import annotations` here.
# FastMCP has issues resolving forward references when PEP 563 deferred annotations
# are used. See: https://github.com/jlowin/fastmcp/issues/905
# Python 3.12+ supports modern type hint syntax natively, so this is not needed.

from dataclasses import dataclass
from typing import Annotated, Literal

from airbyte import constants
from airbyte.exceptions import PyAirbyteInputError
from fastmcp import Context, FastMCP
from fastmcp_extensions import get_mcp_config, mcp_tool, register_mcp_tools
from pydantic import Field

from airbyte_ops_mcp.cloud_admin import api_client
from airbyte_ops_mcp.cloud_admin.auth import (
    CloudAuthError,
    require_internal_admin_flag_only,
)
from airbyte_ops_mcp.cloud_admin.models import (
    ConnectorVersionInfo,
    OrganizationVersionOverrideResult,
    VersionOverrideOperationResult,
    WorkspaceVersionOverrideResult,
)
from airbyte_ops_mcp.constants import ServerConfigKey, WorkspaceAliasEnum
from airbyte_ops_mcp.github_api import (
    GitHubAPIError,
    GitHubCommentParseError,
    GitHubUserEmailNotFoundError,
    get_admin_email_from_approval_comment,
)


@dataclass(frozen=True)
class _ResolvedCloudAuth:
    """Resolved authentication for Airbyte Cloud API calls.

    Either bearer_token OR (client_id AND client_secret) will be set, not both.
    """

    bearer_token: str | None = None
    client_id: str | None = None
    client_secret: str | None = None


def _resolve_cloud_auth(ctx: Context) -> _ResolvedCloudAuth:
    """Resolve authentication credentials for Airbyte Cloud API.

    Credentials are resolved in priority order:
    1. Bearer token (Authorization header or AIRBYTE_CLOUD_BEARER_TOKEN env var)
    2. Client credentials (X-Airbyte-Cloud-Client-Id/Secret headers or env vars)

    Args:
        ctx: FastMCP Context object from the current tool invocation.

    Returns:
        _ResolvedCloudAuth with either bearer_token or client credentials set.

    Raises:
        CloudAuthError: If credentials cannot be resolved from headers or env vars.
    """
    # Try bearer token first (preferred, but not required)
    bearer_token = get_mcp_config(ctx, ServerConfigKey.BEARER_TOKEN)
    if bearer_token:
        return _ResolvedCloudAuth(bearer_token=bearer_token)

    # Fall back to client credentials
    try:
        client_id = get_mcp_config(ctx, ServerConfigKey.CLIENT_ID)
        client_secret = get_mcp_config(ctx, ServerConfigKey.CLIENT_SECRET)
        return _ResolvedCloudAuth(
            client_id=client_id,
            client_secret=client_secret,
        )
    except ValueError as e:
        raise CloudAuthError(
            f"Failed to resolve credentials. Ensure credentials are provided "
            f"via Authorization header (Bearer token), "
            f"HTTP headers (X-Airbyte-Cloud-Client-Id, X-Airbyte-Cloud-Client-Secret), "
            f"or environment variables. Error: {e}"
        ) from e


@mcp_tool(
    read_only=True,
    idempotent=True,
    open_world=True,
)
def get_cloud_connector_version(
    workspace_id: Annotated[
        str | WorkspaceAliasEnum,
        Field(
            description="The Airbyte Cloud workspace ID (UUID) or alias. "
            "Accepts '@devin-ai-sandbox' as an alias for the Devin AI sandbox workspace."
        ),
    ],
    actor_id: Annotated[
        str, "The ID of the deployed connector (source or destination)"
    ],
    actor_type: Annotated[
        Literal["source", "destination"],
        "The type of connector (source or destination)",
    ],
    *,
    ctx: Context,
) -> ConnectorVersionInfo:
    """Get the current version information for a deployed connector.

    Returns version details including the current version string and whether
    an override (pin) is applied.

    Authentication credentials are resolved in priority order:
    1. Bearer token (Authorization header or AIRBYTE_CLOUD_BEARER_TOKEN env var)
    2. HTTP headers: X-Airbyte-Cloud-Client-Id, X-Airbyte-Cloud-Client-Secret
    3. Environment variables: AIRBYTE_CLOUD_CLIENT_ID, AIRBYTE_CLOUD_CLIENT_SECRET
    """
    # Resolve workspace ID alias
    resolved_workspace_id = WorkspaceAliasEnum.resolve(workspace_id)

    try:
        auth = _resolve_cloud_auth(ctx)

        # Use vendored API client instead of connector.get_connector_version()
        # Use Config API root for version management operations
        # Pass workspace_id to get detailed scoped configuration context
        version_data = api_client.get_connector_version(
            connector_id=actor_id,
            connector_type=actor_type,
            config_api_root=constants.CLOUD_CONFIG_API_ROOT,
            client_id=auth.client_id,
            client_secret=auth.client_secret,
            bearer_token=auth.bearer_token,
            workspace_id=resolved_workspace_id,
        )

        # Determine if version is pinned from scoped config context (more reliable)
        # The API's isVersionOverrideApplied only returns true for USER-created pins,
        # not system-generated pins (e.g., breaking_change origin). Check scopedConfigs
        # for a more accurate picture of whether ANY pin exists.
        scoped_configs = version_data.get("scopedConfigs", {})
        has_any_pin = (
            any(config is not None for config in scoped_configs.values())
            if scoped_configs
            else False
        )

        # Use scoped config existence as the source of truth for "is pinned"
        # Fall back to API's isVersionOverrideApplied if no scoped config data
        is_pinned = (
            has_any_pin if scoped_configs else version_data["isVersionOverrideApplied"]
        )

        return ConnectorVersionInfo(
            connector_id=actor_id,
            connector_type=actor_type,
            version=version_data["dockerImageTag"],
            is_version_pinned=is_pinned,
        )
    except CloudAuthError:
        raise
    except Exception as e:
        raise CloudAuthError(
            f"Failed to get connector version for {actor_type} {actor_id}: {e}"
        ) from e


@mcp_tool(
    destructive=True,
    idempotent=False,
    open_world=True,
)
def set_cloud_connector_version_override(
    workspace_id: Annotated[
        str | WorkspaceAliasEnum,
        Field(
            description="The Airbyte Cloud workspace ID (UUID) or alias. "
            "Accepts '@devin-ai-sandbox' as an alias for the Devin AI sandbox workspace."
        ),
    ],
    actor_id: Annotated[
        str, "The ID of the deployed connector (source or destination)"
    ],
    actor_type: Annotated[
        Literal["source", "destination"],
        "The type of connector (source or destination)",
    ],
    approval_comment_url: Annotated[
        str,
        Field(
            description="URL to a GitHub comment where the admin has explicitly "
            "requested or authorized this deployment. Must be a valid GitHub comment URL. "
            "Required for authorization. The admin email is automatically derived from "
            "the comment author's GitHub profile.",
        ),
    ],
    version: Annotated[
        str | None,
        Field(
            description="The semver version string to pin to (e.g., '0.1.0'). "
            "Must be None if unset is True.",
            default=None,
        ),
    ],
    unset: Annotated[
        bool,
        Field(
            description="If True, removes any existing version override. "
            "Cannot be True if version is provided.",
            default=False,
        ),
    ],
    override_reason: Annotated[
        str | None,
        Field(
            description="Required when setting a version. "
            "Explanation for the override (min 10 characters).",
            default=None,
        ),
    ],
    override_reason_reference_url: Annotated[
        str | None,
        Field(
            description="Optional URL with more context (e.g., issue link).",
            default=None,
        ),
    ],
    issue_url: Annotated[
        str | None,
        Field(
            description="URL to the GitHub issue providing context for this operation. "
            "Must be a valid GitHub URL (https://github.com/...). Required for authorization.",
            default=None,
        ),
    ],
    ai_agent_session_url: Annotated[
        str | None,
        Field(
            description="URL to the AI agent session driving this operation, if applicable. "
            "Provides additional auditability for AI-driven operations.",
            default=None,
        ),
    ],
    *,
    ctx: Context,
) -> VersionOverrideOperationResult:
    """Set or clear a version override for a deployed connector.

    **Admin-only operation** - Requires:
    - AIRBYTE_INTERNAL_ADMIN_FLAG=airbyte.io environment variable
    - issue_url parameter (GitHub issue URL for context)
    - approval_comment_url parameter (GitHub comment URL with approval from an @airbyte.io user)

    The admin user email is automatically derived from the approval_comment_url by:
    1. Fetching the comment from GitHub API to get the author's username
    2. Fetching the user's profile to get their public email
    3. Validating the email is an @airbyte.io address

    You must specify EXACTLY ONE of `version` OR `unset=True`, but not both.
    When setting a version, `override_reason` is required.

    Business rules enforced:
    - Dev versions (-dev): Only creator can unpin their own dev version override
    - Production versions: Require strong justification mentioning customer/support/investigation
    - Release candidates (-rc): Any admin can pin/unpin RC versions

    Authentication credentials are resolved in priority order:
    1. Bearer token (Authorization header or AIRBYTE_CLOUD_BEARER_TOKEN env var)
    2. HTTP headers: X-Airbyte-Cloud-Client-Id, X-Airbyte-Cloud-Client-Secret
    3. Environment variables: AIRBYTE_CLOUD_CLIENT_ID, AIRBYTE_CLOUD_CLIENT_SECRET
    """
    # Resolve workspace ID alias (workspace_id is required, so resolved value is never None)
    resolved_workspace_id = WorkspaceAliasEnum.resolve(workspace_id)
    assert resolved_workspace_id is not None  # Type narrowing: workspace_id is required

    # Validate admin access (check env var flag)
    try:
        require_internal_admin_flag_only()
    except CloudAuthError as e:
        return VersionOverrideOperationResult(
            success=False,
            message=f"Admin authentication failed: {e}",
            connector_id=actor_id,
            connector_type=actor_type,
        )

    # Validate authorization parameters
    validation_errors: list[str] = []

    if not issue_url:
        validation_errors.append(
            "issue_url is required for authorization (GitHub issue URL)"
        )
    elif not issue_url.startswith("https://github.com/"):
        validation_errors.append(
            f"issue_url must be a valid GitHub URL (https://github.com/...), got: {issue_url}"
        )

    if not approval_comment_url.startswith("https://github.com/"):
        validation_errors.append(
            f"approval_comment_url must be a valid GitHub URL, got: {approval_comment_url}"
        )
    elif (
        "#issuecomment-" not in approval_comment_url
        and "#discussion_r" not in approval_comment_url
    ):
        validation_errors.append(
            "approval_comment_url must be a GitHub comment URL "
            "(containing #issuecomment- or #discussion_r)"
        )

    if validation_errors:
        return VersionOverrideOperationResult(
            success=False,
            message="Authorization validation failed: " + "; ".join(validation_errors),
            connector_id=actor_id,
            connector_type=actor_type,
        )

    # Derive admin email from approval comment URL
    try:
        admin_user_email = get_admin_email_from_approval_comment(approval_comment_url)
    except GitHubCommentParseError as e:
        return VersionOverrideOperationResult(
            success=False,
            message=f"Failed to parse approval comment URL: {e}",
            connector_id=actor_id,
            connector_type=actor_type,
        )
    except GitHubAPIError as e:
        return VersionOverrideOperationResult(
            success=False,
            message=f"Failed to fetch approval comment from GitHub: {e}",
            connector_id=actor_id,
            connector_type=actor_type,
        )
    except GitHubUserEmailNotFoundError as e:
        return VersionOverrideOperationResult(
            success=False,
            message=str(e),
            connector_id=actor_id,
            connector_type=actor_type,
        )

    # Build enhanced override reason with audit fields (only for 'set' operations)
    enhanced_override_reason = override_reason
    if not unset and override_reason:
        audit_parts = [override_reason]
        audit_parts.append(f"Issue: {issue_url}")
        audit_parts.append(f"Approval: {approval_comment_url}")
        if ai_agent_session_url:
            audit_parts.append(f"AI Session: {ai_agent_session_url}")
        enhanced_override_reason = " | ".join(audit_parts)

    # Resolve auth and get current version info
    try:
        auth = _resolve_cloud_auth(ctx)

        # Get current version info before the operation
        current_version_data = api_client.get_connector_version(
            connector_id=actor_id,
            connector_type=actor_type,
            config_api_root=constants.CLOUD_CONFIG_API_ROOT,
            client_id=auth.client_id,
            client_secret=auth.client_secret,
            bearer_token=auth.bearer_token,
        )
        current_version = current_version_data["dockerImageTag"]
        was_pinned_before = current_version_data["isVersionOverrideApplied"]

    except CloudAuthError as e:
        return VersionOverrideOperationResult(
            success=False,
            message=f"Failed to resolve credentials or get connector: {e}",
            connector_id=actor_id,
            connector_type=actor_type,
        )

    # Call vendored API client's set_connector_version_override method
    try:
        result = api_client.set_connector_version_override(
            connector_id=actor_id,
            connector_type=actor_type,
            config_api_root=constants.CLOUD_CONFIG_API_ROOT,
            client_id=auth.client_id,
            client_secret=auth.client_secret,
            workspace_id=resolved_workspace_id,
            version=version,
            unset=unset,
            override_reason=enhanced_override_reason,
            override_reason_reference_url=override_reason_reference_url,
            user_email=admin_user_email,
            bearer_token=auth.bearer_token,
        )

        # Get updated version info after the operation
        updated_version_data = api_client.get_connector_version(
            connector_id=actor_id,
            connector_type=actor_type,
            config_api_root=constants.CLOUD_CONFIG_API_ROOT,
            client_id=auth.client_id,
            client_secret=auth.client_secret,
            bearer_token=auth.bearer_token,
        )
        new_version = updated_version_data["dockerImageTag"] if not unset else None
        is_pinned_after = updated_version_data["isVersionOverrideApplied"]

        if unset:
            if result:
                message = "Successfully cleared version override. Connector will now use default version."
            else:
                message = "No version override was active (nothing to clear)"
        else:
            message = f"Successfully pinned connector to version {version}"

        return VersionOverrideOperationResult(
            success=True,
            message=message,
            connector_id=actor_id,
            connector_type=actor_type,
            previous_version=current_version,
            new_version=new_version,
            was_pinned_before=was_pinned_before,
            is_pinned_after=is_pinned_after,
        )

    except PyAirbyteInputError as e:
        # PyAirbyte raises this for validation errors and permission denials
        return VersionOverrideOperationResult(
            success=False,
            message=str(e),
            connector_id=actor_id,
            connector_type=actor_type,
            previous_version=current_version,
            was_pinned_before=was_pinned_before,
        )
    except Exception as e:
        return VersionOverrideOperationResult(
            success=False,
            message=f"Failed to {'clear' if unset else 'set'} version override: {e}",
            connector_id=actor_id,
            connector_type=actor_type,
            previous_version=current_version,
            was_pinned_before=was_pinned_before,
        )


@mcp_tool(
    destructive=True,
    idempotent=False,
    open_world=True,
)
def set_workspace_connector_version_override(
    workspace_id: Annotated[
        str | WorkspaceAliasEnum,
        Field(
            description="The Airbyte Cloud workspace ID (UUID) or alias. "
            "Accepts '@devin-ai-sandbox' as an alias for the Devin AI sandbox workspace."
        ),
    ],
    connector_name: Annotated[
        str,
        Field(
            description="The connector name (e.g., 'source-github', 'destination-bigquery')."
        ),
    ],
    connector_type: Annotated[
        Literal["source", "destination"],
        "The type of connector (source or destination)",
    ],
    approval_comment_url: Annotated[
        str,
        Field(
            description="URL to a GitHub comment where the admin has explicitly "
            "requested or authorized this deployment. Must be a valid GitHub comment URL. "
            "Required for authorization. The admin email is automatically derived from "
            "the comment author's GitHub profile.",
        ),
    ],
    version: Annotated[
        str | None,
        Field(
            description="The semver version string to pin to (e.g., '0.1.0'). "
            "Must be None if unset is True.",
            default=None,
        ),
    ],
    unset: Annotated[
        bool,
        Field(
            description="If True, removes any existing version override. "
            "Cannot be True if version is provided.",
            default=False,
        ),
    ],
    override_reason: Annotated[
        str | None,
        Field(
            description="Required when setting a version. "
            "Explanation for the override (min 10 characters).",
            default=None,
        ),
    ],
    override_reason_reference_url: Annotated[
        str | None,
        Field(
            description="Optional URL with more context (e.g., issue link).",
            default=None,
        ),
    ],
    issue_url: Annotated[
        str | None,
        Field(
            description="URL to the GitHub issue providing context for this operation. "
            "Must be a valid GitHub URL (https://github.com/...). Required for authorization.",
            default=None,
        ),
    ],
    ai_agent_session_url: Annotated[
        str | None,
        Field(
            description="URL to the AI agent session driving this operation, if applicable. "
            "Provides additional auditability for AI-driven operations.",
            default=None,
        ),
    ],
    *,
    ctx: Context,
) -> WorkspaceVersionOverrideResult:
    """Set or clear a workspace-level version override for a connector type.

    This pins ALL instances of a connector type within a workspace to a specific version.
    For example, pinning 'source-github' at workspace level means all GitHub sources
    in that workspace will use the pinned version.

    **Admin-only operation** - Requires:
    - AIRBYTE_INTERNAL_ADMIN_FLAG=airbyte.io environment variable
    - issue_url parameter (GitHub issue URL for context)
    - approval_comment_url parameter (GitHub comment URL with approval from an @airbyte.io user)

    You must specify EXACTLY ONE of `version` OR `unset=True`, but not both.
    When setting a version, `override_reason` is required.
    """
    # Resolve workspace ID alias (workspace_id is required, so resolved value is never None)
    resolved_workspace_id = WorkspaceAliasEnum.resolve(workspace_id)
    assert resolved_workspace_id is not None  # Type narrowing: workspace_id is required

    # Validate admin access (check env var flag)
    try:
        require_internal_admin_flag_only()
    except CloudAuthError as e:
        return WorkspaceVersionOverrideResult(
            success=False,
            message=f"Admin authentication failed: {e}",
            workspace_id=resolved_workspace_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )

    # Validate authorization parameters
    validation_errors: list[str] = []

    if not issue_url:
        validation_errors.append(
            "issue_url is required for authorization (GitHub issue URL)"
        )
    elif not issue_url.startswith("https://github.com/"):
        validation_errors.append(
            f"issue_url must be a valid GitHub URL (https://github.com/...), got: {issue_url}"
        )

    if not approval_comment_url.startswith("https://github.com/"):
        validation_errors.append(
            f"approval_comment_url must be a valid GitHub URL, got: {approval_comment_url}"
        )
    elif (
        "#issuecomment-" not in approval_comment_url
        and "#discussion_r" not in approval_comment_url
    ):
        validation_errors.append(
            "approval_comment_url must be a GitHub comment URL "
            "(containing #issuecomment- or #discussion_r)"
        )

    if validation_errors:
        return WorkspaceVersionOverrideResult(
            success=False,
            message="Authorization validation failed: " + "; ".join(validation_errors),
            workspace_id=resolved_workspace_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )

    # Derive admin email from approval comment URL
    try:
        admin_user_email = get_admin_email_from_approval_comment(approval_comment_url)
    except GitHubCommentParseError as e:
        return WorkspaceVersionOverrideResult(
            success=False,
            message=f"Failed to parse approval comment URL: {e}",
            workspace_id=resolved_workspace_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )
    except GitHubAPIError as e:
        return WorkspaceVersionOverrideResult(
            success=False,
            message=f"Failed to fetch approval comment from GitHub: {e}",
            workspace_id=resolved_workspace_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )
    except GitHubUserEmailNotFoundError as e:
        return WorkspaceVersionOverrideResult(
            success=False,
            message=str(e),
            workspace_id=resolved_workspace_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )

    # Build enhanced override reason with audit fields (only for 'set' operations)
    enhanced_override_reason = override_reason
    if not unset and override_reason:
        audit_parts = [override_reason]
        audit_parts.append(f"Issue: {issue_url}")
        audit_parts.append(f"Approval: {approval_comment_url}")
        if ai_agent_session_url:
            audit_parts.append(f"AI Session: {ai_agent_session_url}")
        enhanced_override_reason = " | ".join(audit_parts)

    # Resolve auth and call API client
    try:
        auth = _resolve_cloud_auth(ctx)

        result = api_client.set_workspace_connector_version_override(
            workspace_id=resolved_workspace_id,
            connector_name=connector_name,
            connector_type=connector_type,
            config_api_root=constants.CLOUD_CONFIG_API_ROOT,
            client_id=auth.client_id,
            client_secret=auth.client_secret,
            bearer_token=auth.bearer_token,
            version=version,
            unset=unset,
            override_reason=enhanced_override_reason,
            override_reason_reference_url=override_reason_reference_url,
            user_email=admin_user_email,
        )

        if unset:
            if result:
                message = f"Successfully cleared workspace-level version override for {connector_name}."
            else:
                message = f"No workspace-level version override was active for {connector_name} (nothing to clear)"
        else:
            message = f"Successfully pinned {connector_name} to version {version} at workspace level."

        return WorkspaceVersionOverrideResult(
            success=True,
            message=message,
            workspace_id=resolved_workspace_id,
            connector_name=connector_name,
            connector_type=connector_type,
            version=version if not unset else None,
        )

    except PyAirbyteInputError as e:
        return WorkspaceVersionOverrideResult(
            success=False,
            message=str(e),
            workspace_id=resolved_workspace_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )
    except CloudAuthError as e:
        return WorkspaceVersionOverrideResult(
            success=False,
            message=f"Authentication failed: {e}",
            workspace_id=resolved_workspace_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )


@mcp_tool(
    destructive=True,
    idempotent=False,
    open_world=True,
)
def set_organization_connector_version_override(
    organization_id: Annotated[
        str,
        Field(description="The Airbyte Cloud organization ID."),
    ],
    connector_name: Annotated[
        str,
        Field(
            description="The connector name (e.g., 'source-github', 'destination-bigquery')."
        ),
    ],
    connector_type: Annotated[
        Literal["source", "destination"],
        "The type of connector (source or destination)",
    ],
    approval_comment_url: Annotated[
        str,
        Field(
            description="URL to a GitHub comment where the admin has explicitly "
            "requested or authorized this deployment. Must be a valid GitHub comment URL. "
            "Required for authorization. The admin email is automatically derived from "
            "the comment author's GitHub profile.",
        ),
    ],
    version: Annotated[
        str | None,
        Field(
            description="The semver version string to pin to (e.g., '0.1.0'). "
            "Must be None if unset is True.",
            default=None,
        ),
    ],
    unset: Annotated[
        bool,
        Field(
            description="If True, removes any existing version override. "
            "Cannot be True if version is provided.",
            default=False,
        ),
    ],
    override_reason: Annotated[
        str | None,
        Field(
            description="Required when setting a version. "
            "Explanation for the override (min 10 characters).",
            default=None,
        ),
    ],
    override_reason_reference_url: Annotated[
        str | None,
        Field(
            description="Optional URL with more context (e.g., issue link).",
            default=None,
        ),
    ],
    issue_url: Annotated[
        str | None,
        Field(
            description="URL to the GitHub issue providing context for this operation. "
            "Must be a valid GitHub URL (https://github.com/...). Required for authorization.",
            default=None,
        ),
    ],
    ai_agent_session_url: Annotated[
        str | None,
        Field(
            description="URL to the AI agent session driving this operation, if applicable. "
            "Provides additional auditability for AI-driven operations.",
            default=None,
        ),
    ],
    *,
    ctx: Context,
) -> OrganizationVersionOverrideResult:
    """Set or clear an organization-level version override for a connector type.

    This pins ALL instances of a connector type across an entire organization to a
    specific version. For example, pinning 'source-github' at organization level means
    all GitHub sources in all workspaces within that organization will use the pinned version.

    **Admin-only operation** - Requires:
    - AIRBYTE_INTERNAL_ADMIN_FLAG=airbyte.io environment variable
    - issue_url parameter (GitHub issue URL for context)
    - approval_comment_url parameter (GitHub comment URL with approval from an @airbyte.io user)

    You must specify EXACTLY ONE of `version` OR `unset=True`, but not both.
    When setting a version, `override_reason` is required.
    """
    # Validate admin access (check env var flag)
    try:
        require_internal_admin_flag_only()
    except CloudAuthError as e:
        return OrganizationVersionOverrideResult(
            success=False,
            message=f"Admin authentication failed: {e}",
            organization_id=organization_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )

    # Validate authorization parameters
    validation_errors: list[str] = []

    if not issue_url:
        validation_errors.append(
            "issue_url is required for authorization (GitHub issue URL)"
        )
    elif not issue_url.startswith("https://github.com/"):
        validation_errors.append(
            f"issue_url must be a valid GitHub URL (https://github.com/...), got: {issue_url}"
        )

    if not approval_comment_url.startswith("https://github.com/"):
        validation_errors.append(
            f"approval_comment_url must be a valid GitHub URL, got: {approval_comment_url}"
        )
    elif (
        "#issuecomment-" not in approval_comment_url
        and "#discussion_r" not in approval_comment_url
    ):
        validation_errors.append(
            "approval_comment_url must be a GitHub comment URL "
            "(containing #issuecomment- or #discussion_r)"
        )

    if validation_errors:
        return OrganizationVersionOverrideResult(
            success=False,
            message="Authorization validation failed: " + "; ".join(validation_errors),
            organization_id=organization_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )

    # Derive admin email from approval comment URL
    try:
        admin_user_email = get_admin_email_from_approval_comment(approval_comment_url)
    except GitHubCommentParseError as e:
        return OrganizationVersionOverrideResult(
            success=False,
            message=f"Failed to parse approval comment URL: {e}",
            organization_id=organization_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )
    except GitHubAPIError as e:
        return OrganizationVersionOverrideResult(
            success=False,
            message=f"Failed to fetch approval comment from GitHub: {e}",
            organization_id=organization_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )
    except GitHubUserEmailNotFoundError as e:
        return OrganizationVersionOverrideResult(
            success=False,
            message=str(e),
            organization_id=organization_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )

    # Build enhanced override reason with audit fields (only for 'set' operations)
    enhanced_override_reason = override_reason
    if not unset and override_reason:
        audit_parts = [override_reason]
        audit_parts.append(f"Issue: {issue_url}")
        audit_parts.append(f"Approval: {approval_comment_url}")
        if ai_agent_session_url:
            audit_parts.append(f"AI Session: {ai_agent_session_url}")
        enhanced_override_reason = " | ".join(audit_parts)

    # Resolve auth and call API client
    try:
        auth = _resolve_cloud_auth(ctx)

        result = api_client.set_organization_connector_version_override(
            organization_id=organization_id,
            connector_name=connector_name,
            connector_type=connector_type,
            config_api_root=constants.CLOUD_CONFIG_API_ROOT,
            client_id=auth.client_id,
            client_secret=auth.client_secret,
            bearer_token=auth.bearer_token,
            version=version,
            unset=unset,
            override_reason=enhanced_override_reason,
            override_reason_reference_url=override_reason_reference_url,
            user_email=admin_user_email,
        )

        if unset:
            if result:
                message = f"Successfully cleared organization-level version override for {connector_name}."
            else:
                message = f"No organization-level version override was active for {connector_name} (nothing to clear)"
        else:
            message = f"Successfully pinned {connector_name} to version {version} at organization level."

        return OrganizationVersionOverrideResult(
            success=True,
            message=message,
            organization_id=organization_id,
            connector_name=connector_name,
            connector_type=connector_type,
            version=version if not unset else None,
        )

    except PyAirbyteInputError as e:
        return OrganizationVersionOverrideResult(
            success=False,
            message=str(e),
            organization_id=organization_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )
    except CloudAuthError as e:
        return OrganizationVersionOverrideResult(
            success=False,
            message=f"Authentication failed: {e}",
            organization_id=organization_id,
            connector_name=connector_name,
            connector_type=connector_type,
        )


def register_cloud_connector_version_tools(app: FastMCP) -> None:
    """Register cloud connector version management tools with the FastMCP app.

    Args:
        app: FastMCP application instance
    """
    register_mcp_tools(app, mcp_module=__name__)
