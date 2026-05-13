"""End-to-end: OpenClaw is configured with the wrong endpoint.

A common user-side misconfiguration is pasting the Control UI URL
(``http://127.0.0.1:18789/``) into the MCP integration config instead
of using the ``stdio`` transport.
:func:`app.integrations.openclaw._is_probable_openclaw_control_ui_url`
already detects this; this test asserts the canonical "Use mode
`stdio`" hint propagates through use_case → orchestrator → RCA.

No live Gateway or MCP bridge is needed — the failure surfaces from
``validate_openclaw_config`` alone. So unlike ``test_gateway_down``,
this scenario doesn't even need ``openclaw`` on PATH for the use_case
sub-test (it skips just to keep the suite uniform across scenarios).
"""

from __future__ import annotations

import os

import pytest

from tests.e2e.openclaw.infrastructure_sdk.fault_injection import inject_wrong_endpoint
from tests.e2e.openclaw.infrastructure_sdk.local import (
    boot_openclaw,
    openclaw_cli_available,
    teardown_openclaw,
)
from tests.e2e.openclaw.use_case import drive_openclaw_conversation

pytestmark = pytest.mark.e2e


def _llm_credentials_present() -> bool:
    """RCA needs a live LLM call. We accept any of OpenSRE's supported
    keys so contributors with Anthropic / OpenAI / Gemini configured
    can all run the full pipeline.
    """
    return any(
        os.environ.get(var) for var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY")
    )


@pytest.mark.skipif(
    not openclaw_cli_available(),
    reason="openclaw CLI not installed — see tests/e2e/openclaw/README.md",
)
def test_wrong_endpoint_use_case_captures_validation_hint() -> None:
    """Misconfigured streamable-http URL targeting the Control UI port
    must fail ``validate_openclaw_config`` with the canonical "use mode
    `stdio`" hint.

    Exercises the use_case + fault-injection wiring without depending
    on an LLM. Locks in the failure-context dict shape that the
    orchestrator consumes for the wrong-endpoint scenario.
    """
    handle = boot_openclaw(with_gateway=False)
    try:
        inject_wrong_endpoint(handle)
        context = drive_openclaw_conversation(handle)
    finally:
        teardown_openclaw(handle)

    assert context["failure_mode"] == "wrong_endpoint", context
    assert context["transport_mode"] == "streamable-http"
    assert context["url"] == "http://127.0.0.1:18789"  # config normalizes trailing slash
    # The validation message must contain BOTH the Control-UI flag
    # ("Control UI") and the actionable remediation (the stdio hint).
    detail = context["error_detail"].lower()
    assert "control ui" in detail, context
    assert "stdio" in detail, context
    assert "openclaw" in detail, context


@pytest.mark.skipif(
    not openclaw_cli_available(),
    reason="openclaw CLI not installed — see tests/e2e/openclaw/README.md",
)
@pytest.mark.skipif(
    not _llm_credentials_present(),
    reason=(
        "No LLM credential set (ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY) "
        "— full RCA invocation skipped."
    ),
)
def test_wrong_endpoint_investigation_steers_user_to_stdio() -> None:
    """Run the full OpenSRE investigation against the captured
    misconfiguration. Asserts the RCA names OpenClaw + flags the
    Control-UI mistake + recommends switching to the stdio bridge.

    Real LLM call inside — count this as an integration cost when
    running locally. Skipped when no LLM credential is configured.
    """
    from tests.e2e.openclaw.orchestrator import run_openclaw_investigation

    handle = boot_openclaw(with_gateway=False)
    try:
        inject_wrong_endpoint(handle)
        failure_context = drive_openclaw_conversation(handle)
        assert failure_context["failure_mode"] == "wrong_endpoint"
        result = run_openclaw_investigation(handle, failure_context)
    finally:
        teardown_openclaw(handle)

    summary_text = " ".join(
        str(result.get(key, "")) for key in ("root_cause", "problem_md", "slack_message")
    ).lower()
    assert "openclaw" in summary_text, result
    # The RCA should call out either the Control UI mistake or the
    # stdio remediation — we accept either as evidence the misconfig
    # hint propagated through the investigation surface.
    remediation_text = str(result.get("remediation_steps", result.get("remediation", ""))).lower()
    combined = summary_text + " " + remediation_text
    assert ("control ui" in combined) or ("stdio" in combined), result

    validity_score = result.get("validity_score", 0)
    assert validity_score > 0.7, f"validity_score {validity_score} below 0.7 bar: {result}"
