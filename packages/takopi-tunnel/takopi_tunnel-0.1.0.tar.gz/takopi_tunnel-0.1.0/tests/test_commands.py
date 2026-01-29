"""Integration tests for command handling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from takopi_tunnel.backend import (
    BACKEND,
    HELP_TEXT,
    INSTALL_HELP,
    TUNNELS,
    TunnelCommand,
    TunnelInfo,
    _cleanup_crashed_tunnels,
    _killall,
    _list_tunnels,
    _stop_tunnel,
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
    # Handle both string and RenderedMessage
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


class TestBackendMetadata:
    """Tests for backend metadata."""

    def test_backend_id(self) -> None:
        """Backend should have correct id."""
        assert BACKEND.id == "tunnel"

    def test_backend_description(self) -> None:
        """Backend should have a description."""
        assert BACKEND.description == "manage cloudflared tunnels"

    def test_backend_is_tunnel_command(self) -> None:
        """Backend should be TunnelCommand instance."""
        assert isinstance(BACKEND, TunnelCommand)


class TestHelpCommand:
    """Tests for help command."""

    async def test_no_args_shows_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No arguments should show help."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=())
        result = await BACKEND.handle(ctx)
        assert result is None
        assert ctx.executor.send.called
        sent_text = get_sent_text(ctx)
        assert "Tunnel Commands" in sent_text

    async def test_help_command_shows_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Help command should show help."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("help",))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "Tunnel Commands" in sent_text

    async def test_help_command_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Help command should be case insensitive."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("HELP",))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "Tunnel Commands" in sent_text


class TestCloudflaredCheck:
    """Tests for cloudflared installation check."""

    async def test_shows_install_help_when_not_installed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show install help when cloudflared not installed."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: False)
        ctx = make_context(args=("list",))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "cloudflared not installed" in sent_text


class TestStartCommand:
    """Tests for start command."""

    async def test_start_requires_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Start command should require a port argument."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("start",))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "Usage:" in sent_text

    async def test_start_validates_port_is_number(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Start command should validate port is a number."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("start", "abc"))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "Invalid port number" in sent_text

    async def test_start_validates_port_range_low(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Start command should reject port 0."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("start", "0"))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "Invalid port number" in sent_text

    async def test_start_validates_port_range_high(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Start command should reject port > 65535."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("start", "65536"))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "Invalid port number" in sent_text

    async def test_start_rejects_negative_port(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Start command should reject negative port."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("start", "-1"))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "Invalid port number" in sent_text


class TestStopCommand:
    """Tests for stop command."""

    async def test_stop_requires_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stop command should require a port argument."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("stop",))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "Usage:" in sent_text

    async def test_stop_validates_port_is_number(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Stop command should validate port is a number."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("stop", "abc"))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "Invalid port number" in sent_text

    async def test_stop_nonexistent_tunnel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stop command should handle nonexistent tunnel."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("stop", "9999"))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "No tunnel running for port" in sent_text
        assert "9999" in sent_text


class TestListCommand:
    """Tests for list command."""

    async def test_list_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """List should show message when no tunnels."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("list",))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "No active tunnels" in sent_text

    async def test_list_shows_tunnels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """List should show active tunnels."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)

        # Create fake tunnel
        mock_process = MagicMock()
        mock_process.returncode = None
        TUNNELS[3000] = TunnelInfo(
            port=3000,
            process=mock_process,
            url="https://test-url.trycloudflare.com",
            started_at=datetime.now(timezone.utc),
            channel_id=123,
            thread_id=456,
        )

        ctx = make_context(args=("list",))
        await _list_tunnels(ctx)
        sent_text = get_sent_text(ctx)
        assert "3000" in sent_text
        assert "test-url.trycloudflare.com" in sent_text
        assert "Uptime:" in sent_text


class TestKillallCommand:
    """Tests for killall command."""

    async def test_killall_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Killall should handle no tunnels."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("killall",))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "No active tunnels to stop" in sent_text


class TestUnknownCommand:
    """Tests for unknown commands."""

    async def test_unknown_command_shows_help(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unknown command should show help with error."""
        monkeypatch.setattr("takopi_tunnel.backend._check_cloudflared", lambda: True)
        ctx = make_context(args=("unknown",))
        result = await BACKEND.handle(ctx)
        assert result is None
        sent_text = get_sent_text(ctx)
        assert "Unknown action" in sent_text
        assert "unknown" in sent_text


class TestCleanupCrashedTunnels:
    """Tests for _cleanup_crashed_tunnels function."""

    def test_cleanup_removes_crashed_tunnels(self) -> None:
        """Should remove tunnels with non-None returncode."""
        mock_process = MagicMock()
        mock_process.returncode = 1  # Crashed

        TUNNELS[3000] = TunnelInfo(
            port=3000,
            process=mock_process,
            url="https://test.trycloudflare.com",
            started_at=datetime.now(timezone.utc),
            channel_id=123,
            thread_id=None,
        )

        crashed = _cleanup_crashed_tunnels()
        assert crashed == [3000]
        assert 3000 not in TUNNELS

    def test_cleanup_keeps_running_tunnels(self) -> None:
        """Should keep tunnels with None returncode."""
        mock_process = MagicMock()
        mock_process.returncode = None  # Still running

        TUNNELS[3000] = TunnelInfo(
            port=3000,
            process=mock_process,
            url="https://test.trycloudflare.com",
            started_at=datetime.now(timezone.utc),
            channel_id=123,
            thread_id=None,
        )

        crashed = _cleanup_crashed_tunnels()
        assert crashed == []
        assert 3000 in TUNNELS

    def test_cleanup_handles_mixed_tunnels(self) -> None:
        """Should handle mix of running and crashed tunnels."""
        running_process = MagicMock()
        running_process.returncode = None

        crashed_process = MagicMock()
        crashed_process.returncode = 1

        TUNNELS[3000] = TunnelInfo(
            port=3000,
            process=running_process,
            url="https://running.trycloudflare.com",
            started_at=datetime.now(timezone.utc),
            channel_id=123,
            thread_id=None,
        )
        TUNNELS[4000] = TunnelInfo(
            port=4000,
            process=crashed_process,
            url="https://crashed.trycloudflare.com",
            started_at=datetime.now(timezone.utc),
            channel_id=123,
            thread_id=None,
        )

        crashed = _cleanup_crashed_tunnels()
        assert crashed == [4000]
        assert 3000 in TUNNELS
        assert 4000 not in TUNNELS


class TestListWithCrashedTunnels:
    """Tests for list command with crashed tunnels."""

    async def test_list_reports_crashed_tunnels(self) -> None:
        """List should report and clean up crashed tunnels."""
        crashed_process = MagicMock()
        crashed_process.returncode = 1

        TUNNELS[3000] = TunnelInfo(
            port=3000,
            process=crashed_process,
            url="https://crashed.trycloudflare.com",
            started_at=datetime.now(timezone.utc),
            channel_id=123,
            thread_id=None,
        )

        ctx = make_context(args=("list",))
        await _list_tunnels(ctx)
        sent_text = get_sent_text(ctx)
        assert "Crashed tunnels cleaned up" in sent_text
        assert "3000" in sent_text
        assert "No active tunnels remaining" in sent_text
        assert 3000 not in TUNNELS
