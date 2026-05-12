"""Build an alert from captured failure context and invoke the OpenSRE
investigation pipeline.

Sits between :mod:`use_case` (which captures the failure) and the
scenario tests (which assert on the investigation output). Mirrors the
``trigger-real-failure → invoke-investigation → assert-RCA-quality``
pattern used by :mod:`tests.e2e.crashloop` and
:mod:`tests.e2e.upstream_lambda`.

Stub only — implemented alongside the first fault scenario PR.
"""

from __future__ import annotations

from typing import Any

from tests.e2e.openclaw.infrastructure_sdk.local import OpenClawHandle


def run_openclaw_investigation(
    handle: OpenClawHandle, failure_context: dict[str, Any]
) -> dict[str, Any]:
    """Build an alert from ``failure_context`` and run the OpenSRE pipeline.

    Wraps ``app.cli.investigation.run_rca`` (or the equivalent
    pipeline entry) inside a ``@traceable`` block so the run shows up
    in LangSmith. Annotates the alert with ``context_sources="openclaw"``
    so the investigation knows to weight OpenClaw evidence and surface
    the OpenClaw-specific error hints from
    :func:`app.integrations.openclaw.describe_openclaw_error`.

    Returns the final agent state dict the scenario test then asserts
    on (typically: ``root_cause``, ``problem_md``, ``remediation``,
    ``validity_score``).

    TODO(#issue-3): implement.
    """
    raise NotImplementedError(
        "run_openclaw_investigation stub — implemented in the first scenario PR"
    )
