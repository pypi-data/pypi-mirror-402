"""Tests for subprocess management."""

from __future__ import annotations

import os
import signal
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from takopi_tunnel.backend import (
    TUNNELS,
    TunnelInfo,
    _terminate_process,
    _stop_tunnel,
    _killall,
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
    TUNNELS.clear()


class TestTerminateProcess:
    """Tests for _terminate_process function."""

    def test_does_nothing_if_already_exited(self) -> None:
        """Should not try to terminate if process already exited."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.pid = 1234

        # Should not raise
        _terminate_process(mock_process)
        mock_process.terminate.assert_not_called()

    @pytest.mark.skipif(os.name != "posix", reason="POSIX only")
    def test_uses_killpg_on_posix(self) -> None:
        """Should use killpg on POSIX systems."""
        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.pid = 1234

        with patch("os.killpg") as mock_killpg:
            _terminate_process(mock_process)
            mock_killpg.assert_called_once_with(1234, signal.SIGTERM)
            mock_process.terminate.assert_not_called()

    @pytest.mark.skipif(os.name != "posix", reason="POSIX only")
    def test_handles_process_not_found_on_posix(self) -> None:
        """Should handle ProcessLookupError gracefully."""
        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.pid = 1234

        with patch("os.killpg", side_effect=ProcessLookupError):
            # Should not raise
            _terminate_process(mock_process)

    @pytest.mark.skipif(os.name != "posix", reason="POSIX only")
    def test_falls_back_to_terminate_on_oserror(self) -> None:
        """Should fall back to terminate() on OSError."""
        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.pid = 1234

        with patch("os.killpg", side_effect=OSError("Permission denied")):
            _terminate_process(mock_process)
            mock_process.terminate.assert_called_once()

    def test_handles_terminate_process_not_found(self) -> None:
        """Should handle ProcessLookupError from terminate()."""
        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.pid = None  # Force fallback to terminate()
        mock_process.terminate.side_effect = ProcessLookupError

        # Should not raise
        _terminate_process(mock_process)


class TestStopTunnel:
    """Tests for _stop_tunnel function."""

    async def test_stop_nonexistent_tunnel(self) -> None:
        """Should return error for nonexistent tunnel."""
        ctx = make_context()
        await _stop_tunnel(ctx, 9999)
        sent_text = get_sent_text(ctx)
        assert "No tunnel running for port" in sent_text
        assert "9999" in sent_text

    async def test_stop_removes_tunnel_from_dict(self) -> None:
        """Should remove tunnel from TUNNELS dict."""
        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.pid = None
        mock_process.wait = AsyncMock()

        TUNNELS[3000] = TunnelInfo(
            port=3000,
            process=mock_process,
            url="https://test.trycloudflare.com",
            started_at=datetime.now(timezone.utc),
            channel_id=123,
            thread_id=None,
        )

        ctx = make_context()
        await _stop_tunnel(ctx, 3000)
        sent_text = get_sent_text(ctx)
        assert "3000" in sent_text
        assert "stopped" in sent_text
        assert 3000 not in TUNNELS

    async def test_stop_terminates_process(self) -> None:
        """Should terminate the process."""
        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.pid = None
        mock_process.wait = AsyncMock()

        TUNNELS[3000] = TunnelInfo(
            port=3000,
            process=mock_process,
            url="https://test.trycloudflare.com",
            started_at=datetime.now(timezone.utc),
            channel_id=123,
            thread_id=None,
        )

        ctx = make_context()
        await _stop_tunnel(ctx, 3000)
        mock_process.terminate.assert_called()


class TestKillall:
    """Tests for _killall function."""

    async def test_killall_empty(self) -> None:
        """Should handle no tunnels."""
        ctx = make_context()
        await _killall(ctx)
        sent_text = get_sent_text(ctx)
        assert "No active tunnels to stop" in sent_text

    async def test_killall_stops_all_tunnels(self) -> None:
        """Should stop all tunnels."""
        for port in [3000, 4000, 5000]:
            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.pid = None
            mock_process.wait = AsyncMock()

            TUNNELS[port] = TunnelInfo(
                port=port,
                process=mock_process,
                url=f"https://test-{port}.trycloudflare.com",
                started_at=datetime.now(timezone.utc),
                channel_id=123,
                thread_id=None,
            )

        ctx = make_context()
        await _killall(ctx)
        sent_text = get_sent_text(ctx)
        assert "3" in sent_text
        assert "tunnel" in sent_text.lower()
        assert len(TUNNELS) == 0

    async def test_killall_returns_correct_count(self) -> None:
        """Should return correct count of stopped tunnels."""
        for port in [3000, 4000]:
            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.pid = None
            mock_process.wait = AsyncMock()

            TUNNELS[port] = TunnelInfo(
                port=port,
                process=mock_process,
                url=f"https://test-{port}.trycloudflare.com",
                started_at=datetime.now(timezone.utc),
                channel_id=123,
                thread_id=None,
            )

        ctx = make_context()
        await _killall(ctx)
        sent_text = get_sent_text(ctx)
        assert "2" in sent_text


class TestTunnelInfo:
    """Tests for TunnelInfo dataclass."""

    def test_tunnel_info_creation(self) -> None:
        """Should create TunnelInfo with all fields."""
        mock_process = MagicMock()
        now = datetime.now(timezone.utc)

        tunnel = TunnelInfo(
            port=3000,
            process=mock_process,
            url="https://test.trycloudflare.com",
            started_at=now,
            channel_id=123,
            thread_id=456,
        )

        assert tunnel.port == 3000
        assert tunnel.process is mock_process
        assert tunnel.url == "https://test.trycloudflare.com"
        assert tunnel.started_at == now
        assert tunnel.channel_id == 123
        assert tunnel.thread_id == 456

    def test_tunnel_info_with_none_thread_id(self) -> None:
        """Should allow None thread_id."""
        mock_process = MagicMock()
        now = datetime.now(timezone.utc)

        tunnel = TunnelInfo(
            port=3000,
            process=mock_process,
            url="https://test.trycloudflare.com",
            started_at=now,
            channel_id=123,
            thread_id=None,
        )

        assert tunnel.thread_id is None

    def test_tunnel_info_with_string_ids(self) -> None:
        """Should allow string channel_id and thread_id."""
        mock_process = MagicMock()
        now = datetime.now(timezone.utc)

        tunnel = TunnelInfo(
            port=3000,
            process=mock_process,
            url="https://test.trycloudflare.com",
            started_at=now,
            channel_id="channel_123",
            thread_id="thread_456",
        )

        assert tunnel.channel_id == "channel_123"
        assert tunnel.thread_id == "thread_456"
