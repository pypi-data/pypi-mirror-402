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

# Server configuration - can be overridden by environment variables
SERVER_HOST = os.environ.get("CLAUDE_BOARD_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("CLAUDE_BOARD_PORT", "8765"))
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
TIMEOUT = 5  # Short timeout for notification


def main() -> int:
    """Main entry point for the session start hook."""
    try:
        # Read hook input from stdin
        input_data = sys.stdin.read()
        if not input_data:
            return 0

        hook_input = json.loads(input_data)

        # Extract session information
        session_id = hook_input.get("session_id", "unknown")
        cwd = hook_input.get("cwd", os.getcwd())

        # Notify server about the new session
        notify_server(session_id, cwd)

        return 0

    except Exception as e:
        # Log error but don't fail the hook
        print(f"Session start hook error: {e}", file=sys.stderr)
        return 0  # Return 0 to not block Claude Code


def notify_server(session_id: str, project_path: str) -> None:
    """Notify the Claude Board server about a new session."""
    try:
        # First, set the active project
        data = json.dumps({
            "project_path": project_path,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{SERVER_URL}/api/projects/active",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            response.read()

        # Also notify via the session notification endpoint if available
        session_data = json.dumps({
            "event": "session_start",
            "session_id": session_id,
            "project_path": project_path,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{SERVER_URL}/api/session/notify",
            data=session_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                response.read()
        except urllib.error.HTTPError as e:
            # 404 is OK - endpoint might not exist yet
            if e.code != 404:
                raise

    except urllib.error.URLError:
        # Server not running - that's OK
        pass
    except Exception as e:
        print(f"Failed to notify server: {e}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
