"""Fault injectors for the OpenClaw end-to-end test suite.

Each scenario gets its own injector. They're independent — issues #3
(gateway down), #5 (hung tool call), and #6 (wrong endpoint) can be
implemented in parallel after the boot helpers (#2) land.

Stubs raise ``NotImplementedError`` until their scenario PR fills them
in. See ``tests/e2e/openclaw/README.md`` for the contract each injector
must satisfy.
"""

from __future__ import annotations

from tests.e2e.openclaw.infrastructure_sdk.local import OpenClawHandle


def inject_gateway_down(handle: OpenClawHandle) -> None:
    """Tear down the Gateway while leaving the MCP bridge alive.

    After this call, ``search_openclaw_conversations`` against the
    handle will fail with ``Connection closed`` / ``ECONNREFUSED`` —
    the exact failure surfaced by
    :func:`app.integrations.openclaw._looks_like_openclaw_gateway_unavailable`.

    Intentionally idempotent: callers may pass a handle booted with
    ``with_gateway=False`` (no Gateway to tear down). In that case this
    function is a no-op.

    TODO(#issue-3): implement.
    """
    raise NotImplementedError("inject_gateway_down stub — implemented in the gateway-down PR")


def inject_hung_tool_call(handle: OpenClawHandle) -> None:
    """Install a fixture MCP tool that sleeps past ``OpenClawConfig.timeout_seconds``.

    Used to verify polling / timeout handling and that the OpenSRE agent
    surfaces a useful "timeout" error rather than blocking forever.

    TODO(#issue-5): implement.
    """
    raise NotImplementedError("inject_hung_tool_call stub — implemented in the hung-tool-call PR")


def inject_wrong_endpoint(handle: OpenClawHandle) -> None:
    """Reconfigure the handle to point at the Control UI port (18789).

    ``validate_openclaw_config`` should detect this via
    :func:`app.integrations.openclaw._is_probable_openclaw_control_ui_url`;
    the e2e asserts the resulting hint propagates through the
    investigation surface.

    TODO(#issue-6): implement.
    """
    raise NotImplementedError("inject_wrong_endpoint stub — implemented in the wrong-endpoint PR")
