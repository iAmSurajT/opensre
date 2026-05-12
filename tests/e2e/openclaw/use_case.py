"""Pure business logic that drives an OpenClaw conversation.

No fixtures, no pytest, no fault injection. Each scenario test composes
this with a fault-injection helper and the OpenSRE investigation runner.

Stub only — implemented alongside the first fault scenario PR (#issue-3,
gateway down), which is the first PR that actually needs to drive a
real OpenClaw conversation.
"""

from __future__ import annotations

from typing import Any

from tests.e2e.openclaw.infrastructure_sdk.local import OpenClawHandle


def drive_openclaw_conversation(handle: OpenClawHandle) -> dict[str, Any]:
    """Run a single OpenClaw tool call against ``handle`` and return the
    captured failure context.

    Calls ``search_openclaw_conversations`` (or another MCP tool, per
    scenario), catches whatever exception fires, and returns a context
    dict shaped for ``orchestrator.run_openclaw_investigation``:

        {
          "tool": "search_openclaw_conversations",
          "transport_mode": "stdio" | "streamable-http" | "sse",
          "command": "...",
          "args": "...",
          "url": "...",
          "last_error": "<exception message>",
        }

    TODO(#issue-3): implement.
    """
    raise NotImplementedError(
        "drive_openclaw_conversation stub — implemented in the first scenario PR"
    )
