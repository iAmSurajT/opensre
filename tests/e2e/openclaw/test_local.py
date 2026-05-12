"""End-to-end pytest entrypoint for the OpenClaw integration suite.

Skips cleanly when the ``openclaw`` CLI is not on ``$PATH`` so the
default contributor flow (``make test-cov``) and CI shards that don't
gate on ``ci:openclaw`` stay green.

Each fault scenario lands in its own ``test_<scenario>.py`` next to this
file (issues #3, #5, #6) so the scenarios are independently mergeable.
This file holds the cross-scenario smoke test that proves the suite is
wired up correctly.
"""

from __future__ import annotations

import shutil

import pytest

# Marker is also applied via ``pytestmark`` so the whole module is
# excluded from ``make test-cov`` (which runs ``-m "not synthetic"`` and
# we explicitly exclude e2e dirs there too — both paths skip this).
pytestmark = pytest.mark.e2e


def _openclaw_cli_available() -> bool:
    return shutil.which("openclaw") is not None


@pytest.mark.skipif(
    not _openclaw_cli_available(),
    reason="openclaw CLI not installed — see tests/e2e/openclaw/README.md",
)
def test_openclaw_e2e_suite_scaffold_smoke() -> None:
    """Smoke test that the e2e package imports without error.

    This is intentionally minimal — it confirms the scaffold is in
    place and the import graph is wired so subsequent scenario PRs
    (#issue-3 gateway-down, #issue-5 hung-tool-call, #issue-6
    wrong-endpoint) can land without re-doing this plumbing.

    Skipped when the ``openclaw`` CLI is absent so contributor laptops
    that haven't installed it can still run the full unit suite.
    """
    from tests.e2e.openclaw import orchestrator, use_case
    from tests.e2e.openclaw.infrastructure_sdk import fault_injection, local

    assert hasattr(local, "boot_openclaw")
    assert hasattr(local, "teardown_openclaw")
    assert hasattr(local, "OpenClawHandle")
    assert hasattr(fault_injection, "inject_gateway_down")
    assert hasattr(fault_injection, "inject_hung_tool_call")
    assert hasattr(fault_injection, "inject_wrong_endpoint")
    assert hasattr(use_case, "drive_openclaw_conversation")
    assert hasattr(orchestrator, "run_openclaw_investigation")
