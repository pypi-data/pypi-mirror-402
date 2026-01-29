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

# Server configuration - can be overridden by environment variables
SERVER_HOST = os.environ.get("CLAUDE_BOARD_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("CLAUDE_BOARD_PORT", "8765"))
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
TIMEOUT = 5  # Short timeout since this shouldn't block


def main() -> None:
    try:
        # Read hook input from stdin
        input_data: dict[str, object] = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Only handle Stop events
    hook_event_raw = input_data.get("hook_event_name", "")
    hook_event = str(hook_event_raw) if hook_event_raw else ""
    if hook_event != "Stop":
        sys.exit(0)

    # Prepare the request
    payload = json.dumps({
        "session_id": input_data.get("session_id", ""),
        "hook_event_name": "Stop",
        "stop_hook_active": input_data.get("stop_hook_active", False),
    }).encode("utf-8")

    try:
        # Send to server (fire and forget, don't wait too long)
        req = urllib.request.Request(
            f"{SERVER_URL}/api/hook",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            # We don't need to do anything with the response
            response.read()

        sys.exit(0)

    except urllib.error.URLError:
        # Server not running - that's OK, just exit
        sys.exit(0)

    except TimeoutError:
        # Timeout - that's OK for Stop hook
        sys.exit(0)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
