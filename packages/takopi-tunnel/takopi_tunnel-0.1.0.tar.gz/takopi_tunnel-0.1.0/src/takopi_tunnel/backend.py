"""Cloudflared tunnel management command backend."""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone

import anyio
from anyio.abc import Process

from takopi.api import CommandContext, CommandResult, get_logger
from takopi.transport import RenderedMessage

logger = get_logger(__name__)


def _html(text: str) -> RenderedMessage:
    """Wrap text in a RenderedMessage with HTML parse mode."""
    return RenderedMessage(text=text, extra={"parse_mode": "HTML"})


HELP_TEXT = (
    "<b>Tunnel Commands</b>\n\n"
    "<code>/tunnel start &lt;port&gt;</code> - start a tunnel for port\n"
    "<code>/tunnel list</code> - show active tunnels\n"
    "<code>/tunnel stop &lt;port&gt;</code> - stop tunnel for port\n"
    "<code>/tunnel killall</code> - stop all tunnels\n"
    "<code>/tunnel help</code> - show this help"
)

INSTALL_HELP = (
    "<b>cloudflared not installed</b>\n\n"
    "Install it with:\n"
    "• macOS: <code>brew install cloudflared</code>\n"
    "• Linux: see cloudflare docs\n"
    "• Download: github.com/cloudflare/cloudflared/releases"
)

URL_PATTERN = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


@dataclass
class TunnelInfo:
    """Information about an active tunnel."""

    port: int
    process: Process
    url: str
    started_at: datetime
    channel_id: int | str
    thread_id: int | str | None


# Global state for active tunnels
TUNNELS: dict[int, TunnelInfo] = {}


def _check_cloudflared() -> bool:
    """Check if cloudflared is installed."""
    return shutil.which("cloudflared") is not None


def _format_uptime(started_at: datetime) -> str:
    """Format uptime in a human-readable way."""
    delta = datetime.now(timezone.utc) - started_at
    total_seconds = int(delta.total_seconds())

    if total_seconds < 60:
        return f"{total_seconds}s"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"


async def _read_url_from_stderr(process: Process, timeout: float = 30.0) -> str | None:
    """Read and parse the tunnel URL from cloudflared's stderr."""
    if process.stderr is None:
        return None

    buffer = b""
    with anyio.move_on_after(timeout):
        async for chunk in process.stderr:
            buffer += chunk
            text = buffer.decode("utf-8", errors="replace")
            match = URL_PATTERN.search(text)
            if match:
                return match.group(0)
    return None


def _cleanup_crashed_tunnels() -> list[int]:
    """Check for crashed tunnels and clean them up. Returns list of crashed ports."""
    crashed = []
    for port, tunnel in list(TUNNELS.items()):
        if tunnel.process.returncode is not None:
            crashed.append(port)
            del TUNNELS[port]
            logger.warning(
                "tunnel.crashed",
                port=port,
                exit_code=tunnel.process.returncode,
            )
    return crashed


def _terminate_process(proc: Process) -> None:
    """Terminate a process and its children."""
    if proc.returncode is not None:
        return

    if os.name == "posix" and proc.pid is not None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass

    try:
        proc.terminate()
    except ProcessLookupError:
        pass


async def _start_tunnel(ctx: CommandContext, port: int) -> None:
    """Start a new tunnel for the given port."""
    # Clean up any crashed tunnels first
    _cleanup_crashed_tunnels()

    if port in TUNNELS:
        await ctx.executor.send(
            _html(f"Tunnel for port <b>{port}</b> is already running."),
            reply_to=ctx.message,
        )
        return

    # Start cloudflared process
    cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"]

    if os.name == "posix":
        proc = await anyio.open_process(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            start_new_session=True,
        )
    else:
        proc = await anyio.open_process(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

    # Wait for URL to appear in stderr
    url = await _read_url_from_stderr(proc, timeout=30.0)

    if url is None:
        # Failed to get URL - process might have crashed
        _terminate_process(proc)
        await ctx.executor.send(
            _html(f"Failed to start tunnel for port <b>{port}</b>. Check if the port is in use."),
            reply_to=ctx.message,
        )
        return

    # Create tunnel info
    tunnel = TunnelInfo(
        port=port,
        process=proc,
        url=url,
        started_at=datetime.now(timezone.utc),
        channel_id=ctx.message.channel_id,
        thread_id=ctx.message.thread_id,
    )
    TUNNELS[port] = tunnel

    logger.info("tunnel.started", port=port, url=url)

    await ctx.executor.send(
        _html(f"Tunnel started for port <b>{port}</b>:\n{url}"),
        reply_to=ctx.message,
    )


async def _list_tunnels(ctx: CommandContext) -> None:
    """List all active tunnels."""
    # Clean up crashed tunnels and report them
    crashed = _cleanup_crashed_tunnels()

    lines = []
    if crashed:
        crashed_str = ", ".join(map(str, crashed))
        lines.append(f"<i>Crashed tunnels cleaned up: {crashed_str}</i>")

    if not TUNNELS:
        if crashed:
            lines.append("\nNo active tunnels remaining.")
        else:
            lines.append("No active tunnels.")
        await ctx.executor.send(_html("\n".join(lines)), reply_to=ctx.message)
        return

    lines.append("<b>Active Tunnels</b>\n")
    for port, tunnel in sorted(TUNNELS.items()):
        uptime = _format_uptime(tunnel.started_at)
        lines.append(
            f"• Port <b>{port}</b>\n"
            f"  {tunnel.url}\n"
            f"  Uptime: {uptime}"
        )

    await ctx.executor.send(_html("\n".join(lines)), reply_to=ctx.message)


async def _stop_tunnel(ctx: CommandContext, port: int) -> None:
    """Stop a tunnel for the given port."""
    if port not in TUNNELS:
        await ctx.executor.send(
            _html(f"No tunnel running for port <b>{port}</b>."),
            reply_to=ctx.message,
        )
        return

    tunnel = TUNNELS.pop(port)

    # Terminate the process
    _terminate_process(tunnel.process)

    # Wait briefly for it to stop
    with anyio.move_on_after(2.0):
        await tunnel.process.wait()

    # Force kill if still running
    if tunnel.process.returncode is None:
        if os.name == "posix" and tunnel.process.pid is not None:
            try:
                os.killpg(tunnel.process.pid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
        else:
            try:
                tunnel.process.kill()
            except ProcessLookupError:
                pass

    logger.info("tunnel.stopped", port=port)
    await ctx.executor.send(
        _html(f"Tunnel for port <b>{port}</b> stopped."),
        reply_to=ctx.message,
    )


async def _killall(ctx: CommandContext) -> None:
    """Stop all active tunnels."""
    if not TUNNELS:
        await ctx.executor.send(
            _html("No active tunnels to stop."),
            reply_to=ctx.message,
        )
        return

    count = len(TUNNELS)
    ports = list(TUNNELS.keys())

    for port in ports:
        tunnel = TUNNELS.pop(port)
        _terminate_process(tunnel.process)
        with anyio.move_on_after(2.0):
            await tunnel.process.wait()
        if tunnel.process.returncode is None:
            if os.name == "posix" and tunnel.process.pid is not None:
                try:
                    os.killpg(tunnel.process.pid, signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass
            else:
                try:
                    tunnel.process.kill()
                except ProcessLookupError:
                    pass
        logger.info("tunnel.stopped", port=port)

    await ctx.executor.send(
        _html(f"Stopped <b>{count}</b> tunnel(s)."),
        reply_to=ctx.message,
    )


class TunnelCommand:
    """Command backend for managing cloudflared tunnels."""

    id = "tunnel"
    description = "manage cloudflared tunnels"

    async def handle(self, ctx: CommandContext) -> CommandResult | None:
        """Handle tunnel commands."""
        # Check if cloudflared is installed
        if not _check_cloudflared():
            await ctx.executor.send(_html(INSTALL_HELP), reply_to=ctx.message)
            return None

        args = ctx.args
        if not args:
            await ctx.executor.send(_html(HELP_TEXT), reply_to=ctx.message)
            return None

        action = args[0].lower()

        if action == "help":
            await ctx.executor.send(_html(HELP_TEXT), reply_to=ctx.message)

        elif action == "start":
            if len(args) < 2:
                await ctx.executor.send(
                    _html("Usage: <code>/tunnel start &lt;port&gt;</code>"),
                    reply_to=ctx.message,
                )
                return None
            try:
                port = int(args[1])
                if port < 1 or port > 65535:
                    raise ValueError("Port out of range")
            except ValueError:
                await ctx.executor.send(
                    _html("Invalid port number. Use 1-65535."),
                    reply_to=ctx.message,
                )
                return None
            await _start_tunnel(ctx, port)

        elif action == "list":
            await _list_tunnels(ctx)

        elif action == "stop":
            if len(args) < 2:
                await ctx.executor.send(
                    _html("Usage: <code>/tunnel stop &lt;port&gt;</code>"),
                    reply_to=ctx.message,
                )
                return None
            try:
                port = int(args[1])
            except ValueError:
                await ctx.executor.send(
                    _html("Invalid port number."),
                    reply_to=ctx.message,
                )
                return None
            await _stop_tunnel(ctx, port)

        elif action == "killall":
            await _killall(ctx)

        else:
            await ctx.executor.send(
                _html(f"Unknown action: <code>{action}</code>\n\n{HELP_TEXT}"),
                reply_to=ctx.message,
            )

        return None


BACKEND = TunnelCommand()
