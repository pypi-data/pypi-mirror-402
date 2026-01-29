#!/usr/bin/env python3
"""
Claude Board Permission Request Hook

This script is called by Claude Code before executing dangerous tools.
It sends the request to the Claude Board server and waits for approval.

Hook Input (stdin): JSON with tool_name, tool_input, etc.
Hook Output (stdout): JSON with permission decision

Exit codes:
- 0: Success (stdout contains JSON response)
- 1: Error (falls back to Claude Code's built-in dialog)
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
TIMEOUT = 58  # Just under Claude Code's 60s timeout

# Tools that are always safe (auto-approve without sending to server)
SAFE_TOOLS = {
    "Glob",
    "Grep",
    "TodoWrite",
    "TodoRead",
    "Task",
    "WebSearch",
    "WebFetch",
}


def get_project_dir() -> str:
    """Get the project directory from environment or current working directory"""
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def is_path_in_project(file_path: str) -> bool:
    """Check if a file path is within the project directory"""
    if not file_path:
        return False
    try:
        project_dir = get_project_dir()
        abs_path = os.path.abspath(os.path.expanduser(file_path))
        project_abs = os.path.abspath(project_dir)
        return abs_path.startswith(project_abs + os.sep) or abs_path == project_abs
    except Exception:
        return False


def is_safe_tool(tool_name: str, tool_input: dict[str, object]) -> bool:
    """
    Determine if a tool call is safe and can be auto-approved.

    Safe tools:
    - Glob, Grep, TodoWrite, etc. (always safe)
    - Read within project directory
    """
    # Always safe tools
    if tool_name in SAFE_TOOLS:
        return True

    # Read is safe if within project directory
    if tool_name == "Read":
        file_path_raw = tool_input.get("file_path", "")
        file_path = str(file_path_raw) if file_path_raw else ""
        return is_path_in_project(file_path)

    return False


def auto_approve_response(hook_event: str) -> dict[str, object]:
    """Generate an auto-approve response"""
    if hook_event == "PreToolUse":
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Auto-approved (safe tool)",
            }
        }
    else:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {"behavior": "allow"},
            }
        }


def ask_user_response(hook_event: str, reason: str = "") -> dict[str, object] | None:
    """Generate a response that asks the user via Claude Code's built-in dialog"""
    if hook_event == "PreToolUse":
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": reason or "Claude Board unavailable",
            }
        }
    else:
        # For PermissionRequest, we can't "ask" - it's either allow or deny
        # So we exit with error to let Claude Code handle it
        return None


def main() -> None:
    try:
        # Read hook input from stdin
        input_data: dict[str, object] = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Handle PreToolUse and PermissionRequest events
    hook_event_raw = input_data.get("hook_event_name", "")
    hook_event = str(hook_event_raw) if hook_event_raw else ""
    if hook_event not in ["PreToolUse", "PermissionRequest"]:
        sys.exit(0)

    tool_name_raw = input_data.get("tool_name", "")
    tool_name = str(tool_name_raw) if tool_name_raw else ""
    tool_input_raw = input_data.get("tool_input", {})
    tool_input: dict[str, object] = tool_input_raw if isinstance(tool_input_raw, dict) else {}

    # Check if this is a safe tool - auto-approve without sending to server
    if is_safe_tool(tool_name, tool_input):
        print(json.dumps(auto_approve_response(hook_event)))
        sys.exit(0)

    # Prepare the request for dangerous tools
    payload = json.dumps({
        "session_id": input_data.get("session_id", ""),
        "hook_event_name": hook_event,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_use_id": input_data.get("tool_use_id", "")
    }).encode("utf-8")

    try:
        # Send to server and wait for response
        req = urllib.request.Request(
            f"{SERVER_URL}/api/hook",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))

            # Output the hook response
            print(json.dumps(result))
            sys.exit(0)

    except urllib.error.URLError as e:
        # Server not running - fall back to asking user
        print(f"Claude Board server not available: {e}", file=sys.stderr)

        # Try to return "ask" response for PreToolUse
        response = ask_user_response(hook_event, "Claude Board server not running")
        if response:
            print(json.dumps(response))
            sys.exit(0)
        else:
            # For PermissionRequest, exit with error
            sys.exit(1)

    except TimeoutError:
        # Timeout - ask user (let Claude Code show its own dialog)
        response = ask_user_response(hook_event, "Claude Board timeout")
        if response:
            print(json.dumps(response))
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
