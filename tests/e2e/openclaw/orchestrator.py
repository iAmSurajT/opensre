"""Build an alert from captured failure context and invoke the OpenSRE
investigation pipeline.

Sits between :mod:`use_case` (which captures the failure) and the
scenario tests (which assert on the investigation output). Mirrors the
``trigger-real-failure → invoke-investigation → assert-RCA-quality``
pattern used by :mod:`tests.e2e.crashloop` and
:mod:`tests.e2e.upstream_lambda`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langsmith import traceable

from app.cli.investigation import run_investigation_cli
from tests.e2e.openclaw.infrastructure_sdk.local import OpenClawHandle

_FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "openclaw_e2e_alert.json"


def _load_alert_template() -> dict[str, Any]:
    """Load the alert template used by every OpenClaw e2e scenario.

    The fixture has placeholder values for the failure annotations that
    each scenario fills in from its captured failure context. Loaded
    fresh on each call so test mutations stay local.
    """
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _annotate_alert(alert: dict[str, Any], failure_context: dict[str, Any]) -> None:
    """Fill the per-failure annotations on the alert payload.

    Updates the in-place dict — the alert payload is one of the inputs
    to ``run_investigation_cli``, and the agent reads these annotations
    to ground its diagnosis on the captured failure rather than
    inventing a plausible-sounding cause.
    """
    annotation_keys = ("failure_mode", "transport_mode", "command", "url", "last_error")
    # Copy "args" into "url" only when the scenario didn't provide one
    # (gateway-down has no URL — the bridge stdio-spawns and finds no
    # Gateway). Keeping the key present lets the agent reason about it.
    annotation_values = {
        "failure_mode": failure_context.get("failure_mode", "unknown"),
        "transport_mode": failure_context.get("transport_mode", ""),
        "command": failure_context.get("command", ""),
        "url": failure_context.get("gateway_url") or failure_context.get("args", ""),
        "last_error": failure_context.get("last_error", ""),
    }
    for alert_entry in alert.get("alert_payload", {}).get("alerts", []):
        annotations = alert_entry.setdefault("annotations", {})
        for key in annotation_keys:
            annotations[key] = annotation_values[key]
    common_annotations = alert.get("alert_payload", {}).setdefault("commonAnnotations", {})
    for key in annotation_keys:
        common_annotations[key] = annotation_values[key]


def run_openclaw_investigation(
    handle: OpenClawHandle,
    failure_context: dict[str, Any],
) -> dict[str, Any]:
    """Build an alert from ``failure_context`` and run the OpenSRE pipeline.

    Wraps :func:`run_investigation_cli` inside a ``@traceable`` block so
    the run shows up in LangSmith with metadata that identifies it as
    an OpenClaw e2e run (handle PIDs, failure mode, correlation id).

    Returns the final agent state dict the scenario test then asserts
    on. Expected keys include ``root_cause``, ``problem_md``, and
    ``remediation``.
    """
    alert = _load_alert_template()
    _annotate_alert(alert, failure_context)

    raw_alert = alert["alert_payload"]
    alert_name = alert["alert_name"]
    pipeline_name = alert["pipeline_name"]
    severity = alert["severity"]

    @traceable(
        run_type="chain",
        name=f"openclaw_e2e_{failure_context.get('failure_mode', 'unknown')}",
        metadata={
            "alert_name": alert_name,
            "pipeline_name": pipeline_name,
            "context_sources": "openclaw",
            "failure_mode": failure_context.get("failure_mode", "unknown"),
            "transport_mode": failure_context.get("transport_mode", ""),
            "gateway_pid": handle.gateway_pid,
            "gateway_url": handle.gateway_url,
            "correlation_id": "openclaw-e2e-001",
        },
    )
    def _invoke() -> dict[str, Any]:
        return run_investigation_cli(
            alert_name=alert_name,
            pipeline_name=pipeline_name,
            severity=severity,
            raw_alert=raw_alert,
        )

    return _invoke()
