"""Boot and tear down a local OpenClaw instance for end-to-end tests.

Stubs only — the real implementation lands in the boot-helpers follow-up
issue. See ``tests/e2e/openclaw/README.md`` for the contract this module
needs to satisfy and the prerequisites callers must provide.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OpenClawHandle:
    """Live handle to a booted local OpenClaw instance.

    Returned by :func:`boot_openclaw` and consumed by every fault
    injector. Fields are populated incrementally — ``bridge_pid`` and
    ``bridge_socket`` are always set; ``gateway_pid`` and ``gateway_url``
    are only set when ``with_gateway=True``.
    """

    bridge_pid: int
    bridge_socket: Path
    gateway_pid: int | None = None
    gateway_url: str | None = None
    extra: dict[str, object] = field(default_factory=dict)


def boot_openclaw(*, with_gateway: bool = True) -> OpenClawHandle:
    """Spawn ``openclaw mcp serve stdio`` + (optionally) ``openclaw gateway run``.

    Blocks until the Gateway HTTP healthcheck endpoint responds (when
    ``with_gateway`` is True). Returns an :class:`OpenClawHandle` whose
    fields callers can pass into :func:`call_openclaw_tool` and
    fault-injection helpers.

    Skips the calling test cleanly via ``pytest.skip(...)`` when the
    ``openclaw`` CLI is not on ``$PATH`` — keeps the suite green on
    contributor machines that haven't installed it yet.

    TODO(#issue-2): implement boot + healthcheck + handle population.
    """
    raise NotImplementedError("boot_openclaw stub — implemented in the boot-helpers PR")


def teardown_openclaw(handle: OpenClawHandle) -> None:
    """Tear down a previously booted OpenClaw instance.

    SIGTERM → 5s grace → SIGKILL. Cleans up socket / temp files. Safe to
    call multiple times (idempotent) and resilient to partial-boot
    failures (e.g. Gateway up, bridge died) — caller can always run
    teardown without checking handle state.

    TODO(#issue-2): implement.
    """
    raise NotImplementedError("teardown_openclaw stub — implemented in the boot-helpers PR")
