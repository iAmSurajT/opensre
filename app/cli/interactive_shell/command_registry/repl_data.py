"""Lazy loaders for verified integrations and LLM settings (repl slash commands)."""

from __future__ import annotations

import os
from typing import Any

_ENV_INTEGRATION_REQUIREMENTS: dict[str, tuple[tuple[str, ...], ...]] = {
    "alertmanager": (("ALERTMANAGER_INSTANCES",), ("ALERTMANAGER_URL",)),
    "argocd": (
        ("ARGOCD_INSTANCES",),
        ("ARGOCD_BASE_URL", "ARGOCD_AUTH_TOKEN"),
        ("ARGOCD_BASE_URL", "ARGOCD_USERNAME", "ARGOCD_PASSWORD"),
    ),
    "aws": (
        ("AWS_INSTANCES",),
        ("AWS_ROLE_ARN",),
        ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"),
    ),
    "azure": (("AZURE_LOG_ANALYTICS_WORKSPACE_ID", "AZURE_LOG_ANALYTICS_TOKEN"),),
    "azure_sql": (("AZURE_SQL_SERVER", "AZURE_SQL_DATABASE"),),
    "betterstack": (("BETTERSTACK_QUERY_ENDPOINT", "BETTERSTACK_USERNAME"),),
    "bitbucket": (("BITBUCKET_WORKSPACE",),),
    "clickhouse": (("CLICKHOUSE_HOST",),),
    "coralogix": (("CORALOGIX_INSTANCES",), ("CORALOGIX_API_KEY",)),
    "datadog": (("DD_INSTANCES",), ("DD_API_KEY", "DD_APP_KEY")),
    "discord": (("DISCORD_BOT_TOKEN",),),
    "github": (("GITHUB_MCP_URL",), ("GITHUB_MCP_COMMAND",)),
    "gitlab": (("GITLAB_ACCESS_TOKEN",),),
    "google_docs": (("GOOGLE_CREDENTIALS_FILE", "GOOGLE_DRIVE_FOLDER_ID"),),
    "grafana": (("GRAFANA_INSTANCES",), ("GRAFANA_INSTANCE_URL", "GRAFANA_READ_TOKEN")),
    "honeycomb": (("HONEYCOMB_INSTANCES",), ("HONEYCOMB_API_KEY",)),
    "jira": (("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"),),
    "kafka": (("KAFKA_BOOTSTRAP_SERVERS",),),
    "mariadb": (("MARIADB_HOST", "MARIADB_DATABASE"),),
    "mongodb": (("MONGODB_CONNECTION_STRING",),),
    "mongodb_atlas": (
        ("MONGODB_ATLAS_PUBLIC_KEY", "MONGODB_ATLAS_PRIVATE_KEY", "MONGODB_ATLAS_PROJECT_ID"),
    ),
    "mysql": (("MYSQL_HOST", "MYSQL_DATABASE"),),
    "openclaw": (("OPENCLAW_MCP_URL",), ("OPENCLAW_MCP_COMMAND",)),
    "openobserve": (
        ("OPENOBSERVE_URL", "OPENOBSERVE_TOKEN"),
        ("OPENOBSERVE_URL", "OPENOBSERVE_USERNAME", "OPENOBSERVE_PASSWORD"),
    ),
    "opensearch": (("OPENSEARCH_URL",),),
    "opsgenie": (("OPSGENIE_API_KEY",),),
    "postgresql": (("POSTGRESQL_HOST", "POSTGRESQL_DATABASE"),),
    "rabbitmq": (("RABBITMQ_HOST", "RABBITMQ_USERNAME"),),
    "sentry": (("SENTRY_ORG_SLUG", "SENTRY_AUTH_TOKEN"),),
    "slack": (("SLACK_WEBHOOK_URL",),),
    "snowflake": (
        ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_TOKEN"),
        ("SNOWFLAKE_ACCOUNT_IDENTIFIER", "SNOWFLAKE_TOKEN"),
    ),
    "splunk": (("SPLUNK_INSTANCES",), ("SPLUNK_URL", "SPLUNK_TOKEN")),
    "telegram": (("TELEGRAM_BOT_TOKEN",),),
    "tracer": (("JWT_TOKEN",),),
    "vercel": (("VERCEL_API_TOKEN",),),
    "victoria_logs": (("VICTORIA_LOGS_URL",),),
}


def _env_group_is_configured(env_group: tuple[str, ...]) -> bool:
    return all(os.getenv(env_name, "").strip() for env_name in env_group)


def load_list_integrations() -> list[dict[str, str]]:
    """Return local integration status without making network calls."""
    from app.integrations.store import load_integrations

    rows: list[dict[str, str]] = []
    seen_services: set[str] = set()

    for record in load_integrations():
        service = str(record.get("service", "")).strip().lower()
        if not service:
            continue
        status = str(record.get("status", "active")).strip().lower() or "active"
        if status == "active":
            rendered_status = "configured"
            detail = "Configured in local store. Run /integrations verify to check connectivity."
        elif status in {"failed", "missing", "misconfigured"}:
            rendered_status = "failed" if status == "misconfigured" else status
            detail = "Stored integration needs attention."
        else:
            continue

        instances = record.get("instances")
        instance_count = len(instances) if isinstance(instances, list) else 0
        instance_detail = f" ({instance_count} instances)" if instance_count > 1 else ""
        rows.append(
            {
                "service": service,
                "source": "local store",
                "status": rendered_status,
                "detail": f"{detail}{instance_detail}",
            }
        )
        seen_services.add(service)

    for service, env_groups in _ENV_INTEGRATION_REQUIREMENTS.items():
        if service in seen_services:
            continue
        if not any(_env_group_is_configured(env_group) for env_group in env_groups):
            continue
        rows.append(
            {
                "service": service,
                "source": "local env",
                "status": "configured",
                "detail": "Configured in local environment. Run /integrations verify to check connectivity.",
            }
        )

    return rows


def load_verified_integrations() -> list[dict[str, str]]:
    """Import lazily so an unconfigured store doesn't slow down every REPL turn."""
    from app.integrations.verify import verify_integrations

    return verify_integrations()


def load_llm_settings() -> Any | None:
    """Best-effort LLM settings load; returns None if env is misconfigured."""
    try:
        from app.config import LLMSettings

        return LLMSettings.from_env()
    except Exception:
        return None


__all__ = ["load_list_integrations", "load_llm_settings", "load_verified_integrations"]
