#!/usr/bin/env python3
"""
Claude Board TODO Sync Hook

PostToolUse hook that syncs TodoWrite tool calls to the Claude Board server.
This allows the web UI to display the current TODO list.

This hook is non-blocking and doesn't interfere with Claude Code
if the server is unavailable.
"""

import json
import os
import sys
import urllib.error
import urllib.request

# Server configuration - can be overridden by environment variables
SERVER_HOST = os.environ.get("CLAUDE_BOARD_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("CLAUDE_BOARD_PORT", "8765"))
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/api/todos"
TIMEOUT = 5  # Short timeout - don't block Claude Code


def main():
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)

        # Check if this is a TodoWrite call
        hook_event = input_data.get("hook_event_name", "")
        tool_name = input_data.get("tool_name", "")

        if hook_event != "PostToolUse" or tool_name != "TodoWrite":
            # Not a TodoWrite call, exit silently
            sys.exit(0)

        # Get the todos from tool_input
        tool_input = input_data.get("tool_input", {})
        todos = tool_input.get("todos", [])

        if not todos:
            sys.exit(0)

        # Send to server
        payload = json.dumps({"todos": todos}).encode("utf-8")

        req = urllib.request.Request(
            SERVER_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                pass  # Success, no output needed
        except urllib.error.URLError:
            # Server not running, ignore silently
            pass
        except TimeoutError:
            # Timeout, ignore silently
            pass

    except Exception:
        # Don't interfere with Claude Code on any error
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
