"""Unit tests for helper functions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from takopi_tunnel.backend import (
    URL_PATTERN,
    _check_cloudflared,
    _format_uptime,
    HELP_TEXT,
    INSTALL_HELP,
)


class TestUrlPattern:
    """Tests for the URL pattern regex."""

    def test_matches_valid_trycloudflare_url(self) -> None:
        """Should match valid trycloudflare URLs."""
        urls = [
            "https://deny-church-reveals-gather.trycloudflare.com",
            "https://abc-123.trycloudflare.com",
            "https://a.trycloudflare.com",
            "https://test-url-here.trycloudflare.com",
        ]
        for url in urls:
            match = URL_PATTERN.search(url)
            assert match is not None, f"Should match: {url}"
            assert match.group(0) == url

    def test_extracts_url_from_log_output(self) -> None:
        """Should extract URL from cloudflared log output."""
        log_line = (
            "2024-01-15T10:30:00Z INF +-----------------------------------------------------------+\n"
            "2024-01-15T10:30:00Z INF |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |\n"
            "2024-01-15T10:30:00Z INF |  https://deny-church-reveals-gather.trycloudflare.com                                      |\n"
        )
        match = URL_PATTERN.search(log_line)
        assert match is not None
        assert match.group(0) == "https://deny-church-reveals-gather.trycloudflare.com"

    def test_does_not_match_invalid_urls(self) -> None:
        """Should not match invalid or non-trycloudflare URLs."""
        invalid = [
            "http://deny-church.trycloudflare.com",  # http not https
            "https://example.com",
            "https://trycloudflare.com",  # no subdomain
            "https://UPPER-case.trycloudflare.com",  # uppercase
            "https://under_score.trycloudflare.com",  # underscore
        ]
        for url in invalid:
            match = URL_PATTERN.search(url)
            # Some might partially match, but we check the full URL doesn't match
            if match:
                assert match.group(0) != url, f"Should not fully match: {url}"


class TestFormatUptime:
    """Tests for the _format_uptime function."""

    def test_seconds_only(self) -> None:
        """Should format seconds correctly."""
        now = datetime.now(timezone.utc)
        started = now - timedelta(seconds=45)
        result = _format_uptime(started)
        assert result == "45s"

    def test_zero_seconds(self) -> None:
        """Should handle zero seconds."""
        now = datetime.now(timezone.utc)
        result = _format_uptime(now)
        assert result == "0s"

    def test_minutes_and_seconds(self) -> None:
        """Should format minutes and seconds."""
        now = datetime.now(timezone.utc)
        started = now - timedelta(minutes=5, seconds=30)
        result = _format_uptime(started)
        assert result == "5m 30s"

    def test_exact_minutes(self) -> None:
        """Should format exact minutes."""
        now = datetime.now(timezone.utc)
        started = now - timedelta(minutes=10)
        result = _format_uptime(started)
        assert result == "10m 0s"

    def test_hours_and_minutes(self) -> None:
        """Should format hours and minutes."""
        now = datetime.now(timezone.utc)
        started = now - timedelta(hours=2, minutes=15, seconds=45)
        result = _format_uptime(started)
        assert result == "2h 15m"

    def test_exact_hours(self) -> None:
        """Should format exact hours."""
        now = datetime.now(timezone.utc)
        started = now - timedelta(hours=3)
        result = _format_uptime(started)
        assert result == "3h 0m"

    def test_many_hours(self) -> None:
        """Should handle many hours."""
        now = datetime.now(timezone.utc)
        started = now - timedelta(hours=48, minutes=30)
        result = _format_uptime(started)
        assert result == "48h 30m"


class TestCheckCloudflared:
    """Tests for the _check_cloudflared function."""

    def test_returns_bool(self) -> None:
        """Should return a boolean."""
        result = _check_cloudflared()
        assert isinstance(result, bool)

    def test_check_cloudflared_with_monkeypatch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return True when cloudflared is found."""
        monkeypatch.setattr("shutil.which", lambda cmd: "/usr/local/bin/cloudflared")
        assert _check_cloudflared() is True

    def test_check_cloudflared_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return False when cloudflared is not found."""
        monkeypatch.setattr("shutil.which", lambda cmd: None)
        assert _check_cloudflared() is False


class TestHelpTexts:
    """Tests for help text constants."""

    def test_help_text_contains_commands(self) -> None:
        """Help text should contain all commands."""
        assert "/tunnel start" in HELP_TEXT
        assert "/tunnel list" in HELP_TEXT
        assert "/tunnel stop" in HELP_TEXT
        assert "/tunnel killall" in HELP_TEXT
        assert "/tunnel help" in HELP_TEXT

    def test_install_help_contains_instructions(self) -> None:
        """Install help should contain installation instructions."""
        assert "cloudflared not installed" in INSTALL_HELP
        assert "brew install cloudflared" in INSTALL_HELP
        assert "github.com/cloudflare/cloudflared" in INSTALL_HELP
