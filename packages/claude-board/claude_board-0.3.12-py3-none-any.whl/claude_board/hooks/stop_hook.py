#!/usr/bin/env python3
"""
Claude Board Stop Hook

This script is called by Claude Code when it finishes responding.
It notifies the Claude Board server so the UI can update accordingly.

Hook Input (stdin): JSON with session_id, hook_event_name, etc.
Hook Output (stdout): None required for Stop hook

Exit codes:
- 0: Success
- 1: Error (non-blocking, Stop hooks can't block)
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime

# Server configuration - can be overridden by environment variables
SERVER_HOST = os.environ.get("CLAUDE_BOARD_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("CLAUDE_BOARD_PORT", "8765"))
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
TIMEOUT = 5  # Short timeout since this shouldn't block

# Debug log file - shared with session_start_hook for easy tracking
DEBUG_LOG = "/tmp/claude_board_session_lifecycle.log"


def log_debug(message: str) -> None:
    """Write debug message to log file."""
    try:
        with open(DEBUG_LOG, "a") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] [STOP] {message}\n")
    except Exception:
        pass


def main() -> None:
    try:
        # Read hook input from stdin
        input_data: dict[str, object] = json.load(sys.stdin)
        log_debug(f"Stop hook received: {json.dumps(input_data, default=str)[:500]}")
    except json.JSONDecodeError as e:
        log_debug(f"JSON decode error: {e}")
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Only handle Stop events
    hook_event_raw = input_data.get("hook_event_name", "")
    hook_event = str(hook_event_raw) if hook_event_raw else ""
    log_debug(f"hook_event_name: {hook_event}")

    if hook_event != "Stop":
        log_debug(f"Ignoring non-Stop event: {hook_event}")
        sys.exit(0)

    # Get session_id and cwd (project_path)
    session_id = str(input_data.get("session_id", ""))
    cwd = str(input_data.get("cwd", os.getcwd()))

    # === PROMINENT SESSION ID LOG ===
    log_debug("=" * 60)
    log_debug(f">>> SESSION STOPPED: {session_id}")
    log_debug(f">>> PROJECT PATH: {cwd}")
    log_debug("=" * 60)

    # Prepare the request
    payload = json.dumps({
        "session_id": session_id,
        "hook_event_name": "Stop",
        "stop_hook_active": input_data.get("stop_hook_active", False),
        "project_path": cwd,  # Include project path for better session matching
    }).encode("utf-8")

    log_debug(f"Sending to {SERVER_URL}/api/hook: {payload.decode()}")

    try:
        # Send to server (fire and forget, don't wait too long)
        req = urllib.request.Request(
            f"{SERVER_URL}/api/hook",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            resp_data = response.read()
            log_debug(f"Response: {resp_data.decode()}")

        log_debug("Stop hook completed successfully")
        sys.exit(0)

    except urllib.error.URLError as e:
        # Server not running - that's OK, just exit
        log_debug(f"URLError (server not running?): {e}")
        sys.exit(0)

    except TimeoutError:
        # Timeout - that's OK for Stop hook
        log_debug("Request timed out")
        sys.exit(0)

    except Exception as e:
        log_debug(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
