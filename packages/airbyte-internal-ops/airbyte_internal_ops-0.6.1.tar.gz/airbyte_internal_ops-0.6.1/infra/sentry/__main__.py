"""
Pulumi Infrastructure as Code for Airbyte's Sentry Configuration.

This module manages multiple Sentry projects for Airbyte, including teams, alerts,
integrations, fingerprint rules, and ownership rules.

SETUP:
------
Before running `pulumi up`, generate the Sentry provider SDK:
    pulumi package add terraform-provider jianyuan/sentry

This uses the Terraform Sentry provider directly (v0.14.8) which supports
fingerprinting_rules, grouping_enhancements, and project_ownership on SentryProject resources.

CONFIGURATION:
--------------
All Sentry configuration is defined as Python constants in this file for better readability
and maintainability. A minimal `Pulumi.prod.yaml` file remains only to document authentication
settings and is not used for defining Sentry resources.

IMPORTANT NOTES:
----------------
1. Fingerprint rules ARE managed by this configuration via the fingerprinting_rules
   property on SentryProject. Changes here will be applied to Sentry.

2. Ownership rules ARE managed by this configuration via the ProjectOwnership resource.
   Changes here will be applied to Sentry.

3. The GitHub integration (sentry.yml workflow) is managed separately in:
   https://github.com/airbytehq/workflow-actions

4. Teams are managed separately in Sentry UI and referenced by slug in projects.

IMPORTING EXISTING RESOURCES:
-----------------------------
To import existing Sentry resources into Pulumi state, use the `pulumi import` command.

Import a team:
    pulumi import sentry:index/team:Team <resource_name> airbytehq/<team-slug>

Import a project:
    pulumi import sentry:index/project:Project <alias> airbytehq/<slug>

Import an alert rule:
    pulumi import sentry:index/issueAlert:IssueAlert <name> airbytehq/<project-slug>/<rule-id>

Import project ownership:
    pulumi import sentry:index/projectOwnership:ProjectOwnership <name> airbytehq/<project-slug>
"""

from typing import Any

import pulumi

# Note: The sentry module is generated locally by running:
#   pulumi package add terraform-provider jianyuan/sentry
# This creates sdks/sentry/ with full support for fingerprinting_rules
import pulumi_sentry as sentry

# Type alias for output variables map
OutputVarsMap = dict[str, Any]

# =============================================================================
# CONSTANTS
# =============================================================================

ORGANIZATION = "airbytehq"

# Project aliases (Pulumi resource names) and slugs (actual Sentry project IDs)
CONNECTOR_INCIDENTS_PROJECT_ALIAS = "connector-incidents"
CONNECTOR_INCIDENTS_PROJECT_ID = "connector-incident-management"
CONNECTOR_CI_PROJECT_ALIAS = "connector-ci"
CONNECTOR_CI_PROJECT_ID = "connectors-ci"
ABCTL_PROJECT_ALIAS = "abctl"
ABCTL_PROJECT_ID = "abctl"
CORAL_AGENTS_PROJECT_ALIAS = "coral-agents"
CORAL_AGENTS_PROJECT_ID = "coral-agents"

# =============================================================================
# PROJECT CONFIGURATIONS
# =============================================================================

# Fingerprint rules for connector-incidents project
# See: https://docs.sentry.io/concepts/data-management/event-grouping/fingerprint-rules/
# See: https://github.com/airbytehq/airbyte-ops-mcp/issues/150
CONNECTOR_INCIDENTS_FINGERPRINTING_RULES = """\
# User-side BigQuery quota errors (e.g. BigQuery free tier)
# No action on us, so we group and ignore these:
message:"Quota exceeded: Your project exceeded quota*" -> user-bigquery-storage-quota-exceeded

# Postgres duplicate key errors - group together (ignore constraint name)
# These vary by table-specific constraint names, causing separate Sentry issues
error.value:"duplicate key value violates unique constraint*" -> postgres-duplicate-key

# BigQuery column rename errors - group together (ignore column/table names)
# Column rename failures for partitioning/clustering columns
error.value:"Column*cannot be renamed*" -> bigquery-column-rename

# Connection refused errors - transient network/infrastructure issues
error.value:"Connection refused*" -> connection-refused

# Broken pipe errors - transient network interruptions
error.value:"Broken pipe*" -> broken-pipe

# Statement timeout errors - group by connector name
# These occur during T+D (typing/deduping) operations and vary by pg_temp_XX schema numbers
# and SQL statement content, causing many separate Sentry issues for the same root cause
error.value:"*canceling statement due to statement timeout*" -> statement-timeout, {{tags.connector_name}}

# PostgreSQL I/O errors - transient connection issues (EOF, connection reset, etc.)
# These vary by the specific operation being performed when the connection drops,
# causing separate Sentry issues for the same root cause
error.value:"*I/O error occurred while sending to the backend*" -> postgres-io-error, {{tags.connector_name}}

# State checksum mismatch errors - group by connector name
# These occur when source state record counts don't match platform tracked counts,
# varying by specific record counts and stream names, causing many separate issues
error.value:"*state record count*does not equal platform tracked record count*" -> state-checksum-mismatch, {{tags.connector_name}}"""

# Grouping enhancements for connector-incidents project
# See: https://docs.sentry.io/concepts/data-management/event-grouping/stack-trace-rules/
CONNECTOR_INCIDENTS_GROUPING_ENHANCEMENTS = """\
# java: mark everything from io.airbyte.* as in-app
stack.module:io.airbyte.* +app

# python: mark everything in a folder with airbyte in it as in-app (/airbyte/integration_code, */airbyte_cdk/*)
stack.abs_path:**/airbyte*/** +app"""

# Ownership rules for connector-incidents project
# See: https://docs.sentry.io/product/issues/ownership-rules/
CONNECTOR_INCIDENTS_OWNERSHIP_RULES = """\
# Auto assign issue owners in order to forward the alerts to the relevant teams
# in order to not miss anything, the alerts for api connectors should be set up as [NOT db-connectors]

# python issues should get auto assigned to api connectors team (team-maintain)
tags.stacktrace_platform:python #team-maintain
tags.connector_language:python #team-maintain
tags.source_type:python #team-maintain
tags.source_type:manifest-only #team-maintain

# Check failures happening on platform will mark stacktrace_platform as java, thus even if connectors are api connectors they'll be classified as db connectors. Adding the following (incomplete) rules to avoid that scenario.
tags.connector_repository:airbyte/source-facebook-marketing #team-maintain
tags.connector_repository:airbyte/source-google-analytics-v4 #team-maintain
tags.connector_repository:airbyte/source-google-ads #team-maintain
tags.connector_repository:airbyte/source-bigquery #team-maintain
tags.connector_repository:airbyte/source-shopify #team-maintain
tags.connector_repository:airbyte/source-declarative-manifest #team-maintain

# connector_language is only set on sources
tags.source_type:java #team-extract

# java and normalization failures should go to either destination or sources
# order is important here, as python errors in normalization will be routed to dbs
tags.failure_origin:destination #team-move
tags.stacktrace_platform:java #team-move"""

# Fingerprint rules for connector-ci project
CONNECTOR_CI_FINGERPRINTING_RULES = """\
error.type:CancelledError -> cancelled-error"""

# Grouping enhancements for connector-ci project
# CI-specific rules for pipx venv paths and incorrect abs_path reporting
CONNECTOR_CI_GROUPING_ENHANCEMENTS = """\
# In CI, because of pipx putting our code within the .venv, Sentry thinks frames are out of app
stack.module:pipelines* +app
stack.module:orchestrator* +app

# Sentry thinks these frames are in-app due to abs_path being incorrectly reported as within our codebase
stack.abs_path:**/<* -app"""

# Grouping enhancements for coral-agents project
# Mark coral_agents modules as in-app for better stack trace grouping
CORAL_AGENTS_GROUPING_ENHANCEMENTS = """\
# python: mark coral_agents modules as in-app
stack.module:coral_agents* +app"""


# =============================================================================
# PROJECTS
# =============================================================================


def define_connector_incidents_project() -> tuple[sentry.Project, OutputVarsMap]:
    """Define the connector-incidents project for connector error monitoring."""
    project = sentry.Project(
        CONNECTOR_INCIDENTS_PROJECT_ALIAS,
        organization=ORGANIZATION,
        name=CONNECTOR_INCIDENTS_PROJECT_ID,
        slug=CONNECTOR_INCIDENTS_PROJECT_ID,
        platform="other",
        teams=[
            "team-extract",
            "gl",
            "team-move",
            "team-integrate",
            "airbyte",
        ],
        fingerprinting_rules=CONNECTOR_INCIDENTS_FINGERPRINTING_RULES,
        grouping_enhancements=CONNECTOR_INCIDENTS_GROUPING_ENHANCEMENTS,
        opts=pulumi.ResourceOptions(protect=True),
    )
    outputs: OutputVarsMap = {
        "projects.connector-incidents.slug": project.slug,
        "projects.connector-incidents.url": project.slug.apply(
            lambda s: f"https://{ORGANIZATION}.sentry.io/projects/{s}/"
        ),
        "projects.connector-incidents.issue_grouping_url": project.slug.apply(
            lambda s: f"https://{ORGANIZATION}.sentry.io/settings/projects/{s}/issue-grouping/"
        ),
    }
    return project, outputs


def define_connector_ci_project() -> tuple[sentry.Project, OutputVarsMap]:
    """Define the connector-ci project for CI/CD pipeline monitoring."""
    project = sentry.Project(
        CONNECTOR_CI_PROJECT_ALIAS,
        organization=ORGANIZATION,
        name=CONNECTOR_CI_PROJECT_ID,
        slug=CONNECTOR_CI_PROJECT_ID,
        platform="python",
        teams=[
            "airbyte",
        ],
        fingerprinting_rules=CONNECTOR_CI_FINGERPRINTING_RULES,
        grouping_enhancements=CONNECTOR_CI_GROUPING_ENHANCEMENTS,
        opts=pulumi.ResourceOptions(protect=True),
    )
    outputs: OutputVarsMap = {
        "projects.connector-ci.slug": project.slug,
        "projects.connector-ci.url": project.slug.apply(
            lambda s: f"https://{ORGANIZATION}.sentry.io/projects/{s}/"
        ),
        "projects.connector-ci.issue_grouping_url": project.slug.apply(
            lambda s: f"https://{ORGANIZATION}.sentry.io/settings/projects/{s}/issue-grouping/"
        ),
    }
    return project, outputs


def define_abctl_project() -> tuple[sentry.Project, OutputVarsMap]:
    """Define the abctl project for CLI tool monitoring."""
    project = sentry.Project(
        ABCTL_PROJECT_ALIAS,
        organization=ORGANIZATION,
        name=ABCTL_PROJECT_ID,
        slug=ABCTL_PROJECT_ID,
        platform="go",
        teams=[
            "airbyte",
        ],
        filters=sentry.ProjectFiltersArgs(
            error_messages=[
                "*kong.ParseError: unexpected argument start",
                "*errors.joinError: failed to determine if any previous psql version exists: error reading pgdata version file*",
                "*values.yaml*no such file or directory*",
                "*values.yml*no such file or directory*",
            ],
        ),
        opts=pulumi.ResourceOptions(protect=True),
    )
    outputs: OutputVarsMap = {
        "projects.abctl.slug": project.slug,
        "projects.abctl.url": project.slug.apply(
            lambda s: f"https://{ORGANIZATION}.sentry.io/projects/{s}/"
        ),
        "projects.abctl.issue_grouping_url": project.slug.apply(
            lambda s: f"https://{ORGANIZATION}.sentry.io/settings/projects/{s}/issue-grouping/"
        ),
    }
    return project, outputs


def define_coral_agents_project() -> tuple[sentry.Project, OutputVarsMap]:
    """Define the coral-agents project for AI agent error monitoring.

    This project monitors the coral-agents application, which provides AI-powered
    agent capabilities for Airbyte. It uses Python/FastAPI and integrates with
    OpenTelemetry for tracing.
    """
    project = sentry.Project(
        CORAL_AGENTS_PROJECT_ALIAS,
        organization=ORGANIZATION,
        name=CORAL_AGENTS_PROJECT_ID,
        slug=CORAL_AGENTS_PROJECT_ID,
        platform="python",
        teams=[
            "airbyte",
        ],
        grouping_enhancements=CORAL_AGENTS_GROUPING_ENHANCEMENTS,
        opts=pulumi.ResourceOptions(
            protect=True,
            import_=f"{ORGANIZATION}/{CORAL_AGENTS_PROJECT_ID}",
        ),
    )
    outputs: OutputVarsMap = {
        "projects.coral-agents.slug": project.slug,
        "projects.coral-agents.url": project.slug.apply(
            lambda s: f"https://{ORGANIZATION}.sentry.io/projects/{s}/"
        ),
        "projects.coral-agents.issue_grouping_url": project.slug.apply(
            lambda s: f"https://{ORGANIZATION}.sentry.io/settings/projects/{s}/issue-grouping/"
        ),
    }
    return project, outputs


def define_connector_incidents_alert_rules(
    project: sentry.Project,
) -> list[sentry.IssueAlert]:
    """Define alert rules for the connector-incidents project.

    These rules were imported from Sentry on 2025-12-22 and match the existing
    production configuration. Uses v2 API fields (structured objects) for better
    readability and type safety.

    Args:
        project: The connector-incidents project resource.

    Returns:
        List of IssueAlert resources.
    """
    return [
        # Alert: API Connectors P0 (SDM, 10+ workspaces affected) (ID: 15976921)
        sentry.IssueAlert(
            "alert-api-connectors-p0-sdm",
            organization=ORGANIZATION,
            project=CONNECTOR_INCIDENTS_PROJECT_ID,
            name="API Connectors P0 (SDM, 10+ workspaces affected)",
            action_match="any",
            filter_match="all",
            frequency=1440,
            owner="team:1838478",
            conditions_v2s=[
                sentry.IssueAlertConditionsV2Args(
                    event_unique_user_frequency=sentry.IssueAlertConditionsV2EventUniqueUserFrequencyArgs(
                        comparison_type="count",
                        interval="1d",
                        value=9,
                    ),
                ),
            ],
            filters_v2s=[
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="failure_origin",
                        match="EQUAL",
                        value="source",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="connector_repository",
                        match="CONTAINS",
                        value="source-declarative-manifest",
                    ),
                ),
            ],
            actions_v2s=[
                sentry.IssueAlertActionsV2Args(
                    pagerduty_notify_service=sentry.IssueAlertActionsV2PagerdutyNotifyServiceArgs(
                        account="139284",
                        service="10250",
                        severity="default",
                    ),
                ),
                sentry.IssueAlertActionsV2Args(
                    slack_notify_service=sentry.IssueAlertActionsV2SlackNotifyServiceArgs(
                        channel="#oncall-bots",
                        workspace="139867",
                    ),
                ),
            ],
            opts=pulumi.ResourceOptions(
                protect=True,
                import_=f"{ORGANIZATION}/{CONNECTOR_INCIDENTS_PROJECT_ID}/15976921",
            ),
        ),
        # Alert: DB Source Connectors P0 (Beta, affecting more than 5 workspaces) (ID: 14868739)
        sentry.IssueAlert(
            "alert-db-source-connectors-p0-beta",
            organization=ORGANIZATION,
            project=CONNECTOR_INCIDENTS_PROJECT_ID,
            name="DB Source Connectors P0 (Beta, affecting more than 5 workspaces)",
            action_match="any",
            filter_match="all",
            frequency=1440,
            owner="team:1199001",
            conditions_v2s=[
                sentry.IssueAlertConditionsV2Args(
                    event_unique_user_frequency=sentry.IssueAlertConditionsV2EventUniqueUserFrequencyArgs(
                        comparison_type="count",
                        interval="1d",
                        value=5,
                    ),
                ),
            ],
            filters_v2s=[
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="connector_release_stage",
                        match="NOT_IN",
                        value="alpha,generally_available,custom",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    assigned_to=sentry.IssueAlertFiltersV2AssignedToArgs(
                        target_type="Team",
                        target_identifier="4509563160690689",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="failure_origin",
                        match="EQUAL",
                        value="source",
                    ),
                ),
            ],
            actions_v2s=[
                sentry.IssueAlertActionsV2Args(
                    pagerduty_notify_service=sentry.IssueAlertActionsV2PagerdutyNotifyServiceArgs(
                        account="139284",
                        service="238987",
                        severity="default",
                    ),
                ),
                sentry.IssueAlertActionsV2Args(
                    slack_notify_service=sentry.IssueAlertActionsV2SlackNotifyServiceArgs(
                        channel="#oncall-bots",
                        workspace="139867",
                    ),
                ),
            ],
            opts=pulumi.ResourceOptions(
                protect=True,
                import_=f"{ORGANIZATION}/{CONNECTOR_INCIDENTS_PROJECT_ID}/14868739",
            ),
        ),
        # Alert: DB Source Connectors P0 (GA, affecting more than 5 workspaces) (ID: 14868697)
        sentry.IssueAlert(
            "alert-db-source-connectors-p0-ga",
            organization=ORGANIZATION,
            project=CONNECTOR_INCIDENTS_PROJECT_ID,
            name="DB Source Connectors P0 (GA, affecting more than 5 workspaces)",
            action_match="any",
            filter_match="all",
            frequency=1440,
            owner="team:1199001",
            conditions_v2s=[
                sentry.IssueAlertConditionsV2Args(
                    event_unique_user_frequency=sentry.IssueAlertConditionsV2EventUniqueUserFrequencyArgs(
                        comparison_type="count",
                        interval="1d",
                        value=5,
                    ),
                ),
            ],
            filters_v2s=[
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="connector_release_stage",
                        match="NOT_IN",
                        value="alpha,beta,custom",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    assigned_to=sentry.IssueAlertFiltersV2AssignedToArgs(
                        target_type="Team",
                        target_identifier="4509563160690689",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="failure_origin",
                        match="EQUAL",
                        value="source",
                    ),
                ),
            ],
            actions_v2s=[
                sentry.IssueAlertActionsV2Args(
                    pagerduty_notify_service=sentry.IssueAlertActionsV2PagerdutyNotifyServiceArgs(
                        account="139284",
                        service="238987",
                        severity="default",
                    ),
                ),
                sentry.IssueAlertActionsV2Args(
                    slack_notify_service=sentry.IssueAlertActionsV2SlackNotifyServiceArgs(
                        channel="#oncall-bots",
                        workspace="139867",
                    ),
                ),
            ],
            opts=pulumi.ResourceOptions(
                protect=True,
                import_=f"{ORGANIZATION}/{CONNECTOR_INCIDENTS_PROJECT_ID}/14868697",
            ),
        ),
        # Alert: Destination Connectors P0 (GA, affecting more than 5 workspaces) (ID: 14866113)
        sentry.IssueAlert(
            "alert-destination-connectors-p0-ga",
            organization=ORGANIZATION,
            project=CONNECTOR_INCIDENTS_PROJECT_ID,
            name="Destination Connectors P0 (GA, affecting more than 5 workspaces)",
            action_match="any",
            filter_match="all",
            frequency=1440,
            owner="team:1199001",
            conditions_v2s=[
                sentry.IssueAlertConditionsV2Args(
                    event_unique_user_frequency=sentry.IssueAlertConditionsV2EventUniqueUserFrequencyArgs(
                        comparison_type="count",
                        interval="1d",
                        value=5,
                    ),
                ),
            ],
            filters_v2s=[
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="connector_release_stage",
                        match="NOT_IN",
                        value="alpha,beta,custom",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    assigned_to=sentry.IssueAlertFiltersV2AssignedToArgs(
                        target_type="Team",
                        target_identifier="1838479",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="failure_origin",
                        match="NOT_EQUAL",
                        value="source",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="stacktrace_platform",
                        match="NOT_EQUAL",
                        value="python",
                    ),
                ),
            ],
            actions_v2s=[
                sentry.IssueAlertActionsV2Args(
                    pagerduty_notify_service=sentry.IssueAlertActionsV2PagerdutyNotifyServiceArgs(
                        account="139284",
                        service="238752",
                        severity="default",
                    ),
                ),
                sentry.IssueAlertActionsV2Args(
                    slack_notify_service=sentry.IssueAlertActionsV2SlackNotifyServiceArgs(
                        channel="#move-sentry-alerts",
                        workspace="139867",
                    ),
                ),
                sentry.IssueAlertActionsV2Args(
                    slack_notify_service=sentry.IssueAlertActionsV2SlackNotifyServiceArgs(
                        channel="#dev-platform-move-alerts",
                        workspace="139867",
                    ),
                ),
            ],
            opts=pulumi.ResourceOptions(
                protect=True,
                import_=f"{ORGANIZATION}/{CONNECTOR_INCIDENTS_PROJECT_ID}/14866113",
            ),
        ),
        # Alert: API Connectors P0 (10+ workspaces affected) (ID: 11478402)
        sentry.IssueAlert(
            "alert-api-connectors-p0",
            organization=ORGANIZATION,
            project=CONNECTOR_INCIDENTS_PROJECT_ID,
            name="API Connectors P0 (10+ workspaces affected)",
            action_match="any",
            filter_match="none",
            frequency=1440,
            owner="team:1838478",
            conditions_v2s=[
                sentry.IssueAlertConditionsV2Args(
                    event_unique_user_frequency=sentry.IssueAlertConditionsV2EventUniqueUserFrequencyArgs(
                        comparison_type="count",
                        interval="1d",
                        value=9,
                    ),
                ),
            ],
            filters_v2s=[
                sentry.IssueAlertFiltersV2Args(
                    assigned_to=sentry.IssueAlertFiltersV2AssignedToArgs(
                        target_type="Team",
                        target_identifier="1838479",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="connector_internal_support_level",
                        match="EQUAL",
                        value="100",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="connector_internal_support_level",
                        match="NOT_SET",
                        value="custom",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="connector_internal_support_level",
                        match="EQUAL",
                        value="200",
                    ),
                ),
            ],
            actions_v2s=[
                sentry.IssueAlertActionsV2Args(
                    pagerduty_notify_service=sentry.IssueAlertActionsV2PagerdutyNotifyServiceArgs(
                        account="139284",
                        service="10250",
                        severity="default",
                    ),
                ),
                sentry.IssueAlertActionsV2Args(
                    slack_notify_service=sentry.IssueAlertActionsV2SlackNotifyServiceArgs(
                        channel="#oncall-bots",
                        workspace="139867",
                    ),
                ),
            ],
            opts=pulumi.ResourceOptions(
                protect=True,
                import_=f"{ORGANIZATION}/{CONNECTOR_INCIDENTS_PROJECT_ID}/11478402",
            ),
        ),
        # Alert: New or Escalating Destination Issues (Slack notification only)
        # Re-enabled per team-move request to receive alerts for destination issues
        # without workspace threshold - triggers on new/escalating issues
        sentry.IssueAlert(
            "alert-destination-issues-slack",
            organization=ORGANIZATION,
            project=CONNECTOR_INCIDENTS_PROJECT_ID,
            name="Alert on New or Escalating Destination Issues",
            action_match="any",
            filter_match="all",
            frequency=5,  # Minimum allowed value (5 minutes)
            environment="production",  # Only trigger for production environment
            owner="team:1199001",  # team-move
            conditions_v2s=[
                sentry.IssueAlertConditionsV2Args(
                    first_seen_event=sentry.IssueAlertConditionsV2FirstSeenEventArgs(),
                ),
                sentry.IssueAlertConditionsV2Args(
                    regression_event=sentry.IssueAlertConditionsV2RegressionEventArgs(),
                ),
                sentry.IssueAlertConditionsV2Args(
                    reappeared_event=sentry.IssueAlertConditionsV2ReappearedEventArgs(),
                ),
            ],
            filters_v2s=[
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="connector_release_stage",
                        match="CONTAINS",
                        value="generally_available",
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    assigned_to=sentry.IssueAlertFiltersV2AssignedToArgs(
                        target_type="Team",
                        target_identifier="1838479",  # team-move
                    ),
                ),
                sentry.IssueAlertFiltersV2Args(
                    tagged_event=sentry.IssueAlertFiltersV2TaggedEventArgs(
                        key="failure_origin",
                        match="CONTAINS",
                        value="destination",
                    ),
                ),
            ],
            actions_v2s=[
                sentry.IssueAlertActionsV2Args(
                    slack_notify_service=sentry.IssueAlertActionsV2SlackNotifyServiceArgs(
                        channel="#dev-platform-move-alerts",
                        workspace="139867",
                        # Note: channel_id is read-only and auto-resolved by Sentry from channel name
                    ),
                ),
            ],
            opts=pulumi.ResourceOptions(
                protect=False,  # New resource, not imported - allow modifications
            ),
        ),
    ]


# =============================================================================
# OWNERSHIP RULES - Project ownership configuration for alert routing
# =============================================================================
# Ownership rules determine which team gets assigned to issues based on tags.
# These rules are used by Sentry to route alerts to the appropriate teams.


def define_connector_incidents_ownership() -> sentry.ProjectOwnership:
    """Define ownership rules for the connector-incidents project."""
    return sentry.ProjectOwnership(
        "connector-incidents-ownership",
        organization=ORGANIZATION,
        project=CONNECTOR_INCIDENTS_PROJECT_ID,
        raw=CONNECTOR_INCIDENTS_OWNERSHIP_RULES,
        fallthrough=False,
        auto_assignment="Auto Assign to Issue Owner",
        codeowners_auto_sync=True,
        opts=pulumi.ResourceOptions(
            protect=True,  # Prevent accidental deletion
        ),
    )


# =============================================================================
# MAIN - Entry point for Pulumi
# =============================================================================


def main() -> None:
    """Main entry point for Pulumi configuration."""
    # Create projects and collect outputs
    connector_incidents_project, connector_incidents_outputs = (
        define_connector_incidents_project()
    )
    _, connector_ci_outputs = define_connector_ci_project()
    _, abctl_outputs = define_abctl_project()
    _, coral_agents_outputs = define_coral_agents_project()

    # Create alert rules for connector-incidents project
    # Note: Alert resources are created for side effects; return value not needed
    define_connector_incidents_alert_rules(connector_incidents_project)

    # Create ownership rules for connector-incidents project
    # Note: Ownership resource is created for side effects; return value not needed
    define_connector_incidents_ownership()

    # Export organization-level outputs
    pulumi.export("organization", ORGANIZATION)
    pulumi.export("alert_rules_url", f"https://{ORGANIZATION}.sentry.io/alerts/rules/")

    # Export combined project outputs
    all_outputs: OutputVarsMap = {
        **connector_incidents_outputs,
        **connector_ci_outputs,
        **abctl_outputs,
        **coral_agents_outputs,
    }
    for key, value in all_outputs.items():
        pulumi.export(key, value)


# Run main when executed by Pulumi
main()
