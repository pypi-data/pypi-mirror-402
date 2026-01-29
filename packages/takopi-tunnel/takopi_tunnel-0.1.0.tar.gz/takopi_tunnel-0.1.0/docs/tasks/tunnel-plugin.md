# Takopi Tunnel Plugin

## Overview

Create a takopi command plugin that manages cloudflared quick tunnels for local development. The plugin allows users to expose local ports via Cloudflare tunnels directly from Telegram.

## Commands

| Command | Description |
|---------|-------------|
| `/tunnel start <port>` | Create and start a tunnel for the specified port |
| `/tunnel list` | Show all active tunnels with their URLs and uptime |
| `/tunnel stop <port>` | Stop the tunnel for the specified port |
| `/tunnel killall` | Stop all active tunnels |
| `/tunnel` or `/tunnel help` | Show help with available commands |

## Design Decisions

### 1. Quick Tunnels (TryCloudflare)
- Use cloudflared's quick tunnel feature (`cloudflared tunnel --url http://localhost:<port>`)
- No authentication or Cloudflare account required
- Each tunnel gets a random `*.trycloudflare.com` subdomain
- Tunnels are ephemeral - they don't persist across restarts (as specified)

### 2. Process Management
- Store tunnel processes in a module-level dictionary keyed by port number
- Use `anyio.open_process()` for async subprocess management
- Parse the tunnel URL from cloudflared's stderr output (it prints the URL there)
- Track start time for uptime display

### 3. Crash Detection
- Run a background task to monitor each tunnel process
- When a process exits unexpectedly, send a notification to the chat
- Store the message context (channel_id, thread_id) for crash notifications

### 4. Startup Check
- On first command invocation, check if `cloudflared` is in PATH
- If not installed, send a helpful message with installation instructions

## Implementation Plan

### Task 1: Project Structure
- [x] Create pyproject.toml with proper entrypoint configuration
- [x] Create src/takopi_tunnel/__init__.py
- [x] Create src/takopi_tunnel/backend.py with command backend

### Task 2: Core Data Structures
- [x] TunnelInfo dataclass: port, process, url, started_at, channel_id, thread_id
- [x] Module-level TUNNELS dict to track active tunnels

### Task 3: Cloudflared Check
- [x] Function to check if cloudflared is installed (shutil.which)
- [x] Return helpful installation message if not found

### Task 4: Start Command
- [x] Parse port from args
- [x] Validate port is a number and not already tunneled
- [x] Start cloudflared subprocess
- [x] Parse URL from stderr output
- [x] Store tunnel info
- [x] Start crash monitor task
- [x] Return formatted success message with URL

### Task 5: List Command
- [x] Iterate over active tunnels
- [x] Format each with port, URL, and uptime
- [x] Handle empty list case

### Task 6: Stop Command
- [x] Parse port from args
- [x] Find and terminate the tunnel process
- [x] Remove from TUNNELS dict
- [x] Return confirmation

### Task 7: Killall Command
- [x] Terminate all tunnel processes
- [x] Clear TUNNELS dict
- [x] Return count of killed tunnels

### Task 8: Help Command
- [x] Return formatted help text with all commands

### Task 9: Crash Monitoring
- [x] Background task that waits for process exit
- [x] On unexpected exit, send notification to original chat
- [x] Clean up tunnel from TUNNELS dict

## File Structure

```
takopi-tunnel/
├── pyproject.toml
├── README.md
├── docs/
│   └── tasks/
│       └── tunnel-plugin.md
├── src/
│   └── takopi_tunnel/
│       ├── __init__.py
│       └── backend.py
└── tests/
    ├── __init__.py
    ├── test_helpers.py      # Unit tests for helper functions
    ├── test_commands.py     # Command handling tests
    ├── test_subprocess.py   # Process management tests
    └── test_integration.py  # Real cloudflared integration tests
```

## Dependencies

- `takopi>=0.14` (for plugin API)
- `anyio` (already a takopi dependency)

### Dev Dependencies
- `pytest>=8.0`
- `pytest-asyncio>=0.24`

## Testing

### Automated Tests (55 tests)

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run all tests
uv run pytest tests/ -v
```

**Test Categories:**
- `test_helpers.py` - URL pattern matching, uptime formatting, cloudflared detection
- `test_commands.py` - Command parsing, validation, help text, error handling
- `test_subprocess.py` - Process termination, cleanup, POSIX signal handling
- `test_integration.py` - Real tunnel lifecycle (requires cloudflared installed)

### Manual Testing
1. Install plugin: `uv pip install -e .`
2. Run takopi
3. Test commands in Telegram

## Notes

- cloudflared quick tunnels print the URL to stderr after ~2 seconds
- The URL format is: `https://<random>.trycloudflare.com`
- We need to read stderr async and parse for the URL pattern
- Process group signaling ensures child processes are also terminated
