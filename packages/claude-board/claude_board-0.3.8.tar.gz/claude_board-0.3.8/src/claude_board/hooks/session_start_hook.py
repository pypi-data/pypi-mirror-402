#!/usr/bin/env python3
"""
Claude Board Session Start Hook

This script is called by Claude Code when a new session starts.
It notifies the Claude Board server about the new session so the UI can display it.

Hook Input (stdin): JSON with session_id, cwd, etc.
Hook Output (stdout): None required (notification only)

Exit codes:
- 0: Success
- Non-zero: Error (logged but doesn't affect Claude Code)
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
TIMEOUT = 5  # Short timeout for notification

# Debug log file - shared with stop_hook for easy tracking
DEBUG_LOG = "/tmp/claude_board_session_lifecycle.log"


def log_debug(message: str) -> None:
    """Write debug message to log file."""
    try:
        with open(DEBUG_LOG, "a") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] [START] {message}\n")
    except Exception:
        pass


def main() -> int:
    """Main entry point for the session start hook."""
    try:
        log_debug("=== Session Start Hook Called ===")

        # Read hook input from stdin
        input_data = sys.stdin.read()
        log_debug(f"Input data: {input_data[:500] if input_data else 'empty'}")

        if not input_data:
            log_debug("No input data, exiting")
            return 0

        hook_input = json.loads(input_data)
        log_debug(f"Parsed hook input: {json.dumps(hook_input, indent=2)}")

        # Extract session information
        session_id = hook_input.get("session_id", "unknown")
        cwd = hook_input.get("cwd", os.getcwd())

        # === PROMINENT SESSION ID LOG ===
        log_debug("=" * 60)
        log_debug(f">>> SESSION STARTED: {session_id}")
        log_debug(f">>> PROJECT PATH: {cwd}")
        log_debug("=" * 60)

        # Notify server about the new session
        notify_server(session_id, cwd)

        log_debug("Hook completed successfully")
        return 0

    except Exception as e:
        # Log error but don't fail the hook
        log_debug(f"Session start hook error: {e}")
        print(f"Session start hook error: {e}", file=sys.stderr)
        return 0  # Return 0 to not block Claude Code


def notify_server(session_id: str, project_path: str) -> None:
    """Notify the Claude Board server about a new session."""
    log_debug(f"notify_server called: session_id={session_id}, project_path={project_path}")

    try:
        # First, set the active project
        data = json.dumps({
            "project_path": project_path,
        }).encode("utf-8")

        log_debug(f"Sending to {SERVER_URL}/api/projects/active: {data.decode()}")

        req = urllib.request.Request(
            f"{SERVER_URL}/api/projects/active",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            resp_data = response.read().decode()
            log_debug(f"Response from /api/projects/active: {resp_data}")

        # Check if this session was started by claude-board chat
        # The chat session sets CLAUDE_BOARD_SESSION_ID env var
        chat_session_id = os.environ.get("CLAUDE_BOARD_SESSION_ID")
        log_debug(f"CLAUDE_BOARD_SESSION_ID env: {chat_session_id}")

        # Also notify via the session notification endpoint if available
        session_data = json.dumps({
            "event": "session_start",
            "session_id": session_id,
            "project_path": project_path,
            "chat_session_id": chat_session_id,  # May be None for external sessions
        }).encode("utf-8")

        log_debug(f"Sending to {SERVER_URL}/api/session/notify: {session_data.decode()}")

        req = urllib.request.Request(
            f"{SERVER_URL}/api/session/notify",
            data=session_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                resp_data = response.read().decode()
                log_debug(f"Response from /api/session/notify: {resp_data}")
        except urllib.error.HTTPError as e:
            log_debug(f"HTTPError from /api/session/notify: {e.code} - {e.reason}")
            # 404 is OK - endpoint might not exist yet
            if e.code != 404:
                raise

    except urllib.error.URLError as e:
        # Server not running - that's OK
        log_debug(f"URLError (server not running?): {e}")
        pass
    except Exception as e:
        log_debug(f"Failed to notify server: {e}")
        print(f"Failed to notify server: {e}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
