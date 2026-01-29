"""Integration tests that use real cloudflared (when available)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from takopi_tunnel.backend import (
    BACKEND,
    TUNNELS,
    _check_cloudflared,
)


# Skip all tests in this module if cloudflared is not installed
pytestmark = pytest.mark.skipif(
    not _check_cloudflared(),
    reason="cloudflared not installed",
)


@dataclass
class FakeMessageRef:
    """Fake MessageRef for testing."""

    channel_id: int | str
    message_id: int | str
    thread_id: int | str | None = None
    raw: Any = None


@dataclass
class FakeCommandContext:
    """Fake CommandContext for testing."""

    command: str
    text: str
    args_text: str
    args: tuple[str, ...]
    message: FakeMessageRef
    reply_to: FakeMessageRef | None
    reply_text: str | None
    config_path: Path | None
    plugin_config: dict[str, Any]
    runtime: Any
    executor: Any


def make_context(
    args: tuple[str, ...] = (),
    channel_id: int = 123,
    thread_id: int | None = 456,
) -> FakeCommandContext:
    """Create a fake command context for testing."""
    executor = AsyncMock()
    return FakeCommandContext(
        command="tunnel",
        text=f"/tunnel {' '.join(args)}",
        args_text=" ".join(args),
        args=args,
        message=FakeMessageRef(channel_id=channel_id, message_id=1, thread_id=thread_id),
        reply_to=None,
        reply_text=None,
        config_path=None,
        plugin_config={},
        runtime=MagicMock(),
        executor=executor,
    )


def get_sent_text(ctx: FakeCommandContext) -> str:
    """Extract the text from the last executor.send() call."""
    if not ctx.executor.send.called:
        return ""
    call_args = ctx.executor.send.call_args
    if call_args is None:
        return ""
    message = call_args[0][0]
    if hasattr(message, "text"):
        return message.text
    return str(message)


@pytest.fixture(autouse=True)
def clear_tunnels():
    """Clear global tunnel state before and after each test."""
    TUNNELS.clear()
    yield
    # Clean up any remaining tunnels
    for tunnel in list(TUNNELS.values()):
        if tunnel.process.returncode is None:
            try:
                tunnel.process.terminate()
            except Exception:
                pass
    TUNNELS.clear()


class TestRealTunnelLifecycle:
    """Integration tests using real cloudflared."""

    async def test_start_list_stop_lifecycle(self) -> None:
        """Test full tunnel lifecycle: start, list, stop."""
        # Start a tunnel on an unused port
        ctx = make_context(args=("start", "19999"))
        result = await BACKEND.handle(ctx)

        assert result is None  # Now returns None, sends via executor
        sent_text = get_sent_text(ctx)
        assert "19999" in sent_text
        assert "trycloudflare.com" in sent_text
        assert 19999 in TUNNELS

        # List tunnels
        ctx = make_context(args=("list",))
        result = await BACKEND.handle(ctx)

        assert result is None
        sent_text = get_sent_text(ctx)
        assert "19999" in sent_text
        assert "trycloudflare.com" in sent_text
        assert "Uptime:" in sent_text

        # Stop the tunnel
        ctx = make_context(args=("stop", "19999"))
        result = await BACKEND.handle(ctx)

        assert result is None
        sent_text = get_sent_text(ctx)
        assert "19999" in sent_text
        assert "stopped" in sent_text
        assert 19999 not in TUNNELS

    async def test_start_duplicate_port(self) -> None:
        """Test starting a tunnel on already-tunneled port."""
        # Start first tunnel
        ctx = make_context(args=("start", "19998"))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "19998" in sent_text
        assert "trycloudflare.com" in sent_text

        # Try to start another on same port
        ctx = make_context(args=("start", "19998"))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "already running" in sent_text

        # Cleanup
        ctx = make_context(args=("stop", "19998"))
        await BACKEND.handle(ctx)

    async def test_killall_multiple_tunnels(self) -> None:
        """Test killall with multiple tunnels."""
        # Start multiple tunnels
        for port in [19990, 19991]:
            ctx = make_context(args=("start", str(port)))
            result = await BACKEND.handle(ctx)
            assert result is None
            sent_text = get_sent_text(ctx)
            assert str(port) in sent_text

        assert len(TUNNELS) == 2

        # Kill all
        ctx = make_context(args=("killall",))
        result = await BACKEND.handle(ctx)

        assert result is None
        sent_text = get_sent_text(ctx)
        assert "2" in sent_text
        assert len(TUNNELS) == 0
