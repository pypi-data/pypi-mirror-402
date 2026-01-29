"""
Data models for Claude Board

Defines the core data structures used across:
- Web UI server
- Bluetooth communication (future)
- State management
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DecisionStatus(str, Enum):
    """Status of a permission request decision"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"


class ConnectionType(str, Enum):
    """Type of client connection"""
    WEB = "web"
    BLUETOOTH = "bluetooth"


@dataclass
class PermissionRequest:
    """A pending permission request from Claude Code"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    tool_input: dict[str, object] = field(default_factory=dict)
    tool_use_id: str = ""
    session_id: str = ""
    project_path: str = ""  # The project directory this request is from
    timestamp: datetime = field(default_factory=datetime.now)
    status: DecisionStatus = DecisionStatus.PENDING

    @property
    def project_name(self) -> str:
        """Get a display name for the project"""
        from pathlib import Path
        if self.project_path:
            return Path(self.project_path).name
        return "unknown"

    def to_display_dict(self) -> dict[str, object]:
        """Convert to frontend-friendly format"""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "display_text": self.get_display_text(),
            "project_path": self.project_path,
            "project_name": self.project_name,
            "session_id": self.session_id,
        }

    def get_display_text(self) -> str:
        """Human-readable description of the request"""
        if self.tool_name == "Bash":
            cmd_raw = self.tool_input.get("command", "unknown")
            cmd = str(cmd_raw) if cmd_raw else "unknown"
            # Truncate long commands
            if len(cmd) > 100:
                cmd = cmd[:97] + "..."
            return f"Bash: {cmd}"
        elif self.tool_name == "Write":
            fp = self.tool_input.get("file_path", "unknown")
            return f"Write: {fp}"
        elif self.tool_name == "Edit":
            fp = self.tool_input.get("file_path", "unknown")
            return f"Edit: {fp}"
        elif self.tool_name == "Read":
            fp = self.tool_input.get("file_path", "unknown")
            return f"Read: {fp}"
        elif self.tool_name == "Glob":
            pattern = self.tool_input.get("pattern", "unknown")
            return f"Glob: {pattern}"
        elif self.tool_name == "Grep":
            pattern = self.tool_input.get("pattern", "unknown")
            return f"Grep: {pattern}"
        else:
            input_str = str(self.tool_input)[:50]
            return f"{self.tool_name}: {input_str}"

    def to_ble_bytes(self) -> bytes:
        """
        Serialize for Bluetooth transmission (future use).

        Format: compact binary for low-bandwidth BLE.
        """
        # Simple JSON for now, can be optimized later with msgpack/protobuf
        data = {
            "id": self.id[:8],  # Shortened ID for BLE
            "tool": self.tool_name,
            "text": self.get_display_text()[:100],
        }
        return json.dumps(data).encode("utf-8")


@dataclass
class CompletedTask:
    """A completed (approved/denied) task"""

    id: str
    tool_name: str
    display_text: str
    timestamp: datetime
    approved: bool
    project_path: str = ""

    @property
    def project_name(self) -> str:
        """Get a display name for the project"""
        from pathlib import Path
        if self.project_path:
            return Path(self.project_path).name
        return "unknown"

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "display_text": self.display_text,
            "timestamp": self.timestamp.isoformat(),
            "approved": self.approved,
            "project_path": self.project_path,
            "project_name": self.project_name,
        }


@dataclass
class SessionStats:
    """Statistics for the current session"""

    start_time: datetime = field(default_factory=datetime.now)
    total_requests: int = 0
    approved_count: int = 0
    denied_count: int = 0

    def to_dict(self) -> dict[str, object]:
        elapsed = datetime.now() - self.start_time
        return {
            "start_time": self.start_time.isoformat(),
            "elapsed_seconds": int(elapsed.total_seconds()),
            "total_requests": self.total_requests,
            "approved_count": self.approved_count,
            "denied_count": self.denied_count,
        }


@dataclass
class ClaudeSession:
    """
    Represents a Claude Code session (external claude CLI invocation).

    This is different from ChatSession which is a PTY session managed by claude-board.
    A ClaudeSession is created when:
    - User runs `claude` command externally
    - session_start_hook notifies us

    It can be linked to a ChatSession if created via claude-board chat.
    """

    session_id: str
    project_path: str
    start_time: datetime = field(default_factory=datetime.now)
    chat_session_id: str | None = None  # Linked ChatSession if any
    is_external: bool = True  # True if started externally (not via claude-board chat)
    ended: bool = False  # True when session has ended (stop hook called)
    end_time: datetime | None = None  # When session ended

    @property
    def project_name(self) -> str:
        """Get a display name for the project"""
        from pathlib import Path
        return Path(self.project_path).name

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "project_path": self.project_path,
            "project_name": self.project_name,
            "start_time": self.start_time.isoformat(),
            "chat_session_id": self.chat_session_id,
            "is_external": self.is_external,
            "ended": self.ended,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class TodoStatus(str, Enum):
    """Status of a todo item"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class TodoItem:
    """A todo item for task tracking"""

    content: str
    status: TodoStatus
    active_form: str  # Present continuous form shown during execution
    project_path: str = ""

    @property
    def project_name(self) -> str:
        """Get a display name for the project"""
        from pathlib import Path
        if self.project_path:
            return Path(self.project_path).name
        return "unknown"

    def to_dict(self) -> dict[str, object]:
        return {
            "content": self.content,
            "status": self.status.value,
            "activeForm": self.active_form,
            "project_path": self.project_path,
            "project_name": self.project_name,
        }


@dataclass
class ConnectedClient:
    """Information about a connected client (web or bluetooth)"""

    id: str
    connection_type: ConnectionType
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "type": self.connection_type.value,
            "connected_at": self.connected_at.isoformat(),
        }


@dataclass
class ProjectState:
    """State for a single project"""

    project_path: str
    pending_requests: list[PermissionRequest] = field(default_factory=list)
    completed_tasks: list[CompletedTask] = field(default_factory=list)
    stats: SessionStats = field(default_factory=SessionStats)
    todos: list[TodoItem] = field(default_factory=list)
    current_task: str | None = None

    # Backward compatibility
    @property
    def pending_request(self) -> PermissionRequest | None:
        """Get the first pending request (for backward compatibility)"""
        return self.pending_requests[0] if self.pending_requests else None

    @property
    def project_name(self) -> str:
        """Get a display name for the project"""
        from pathlib import Path
        return Path(self.project_path).name

    def to_dict(self) -> dict[str, object]:
        return {
            "project_path": self.project_path,
            "project_name": self.project_name,
            "current_task": self.current_task,
            # For backward compatibility, keep pending_request as single item
            "pending_request": (
                self.pending_requests[0].to_display_dict() if self.pending_requests else None
            ),
            # New: all pending requests
            "pending_requests": [r.to_display_dict() for r in self.pending_requests],
            "completed_tasks": [
                t.to_dict() for t in self.completed_tasks[-10:]
            ],  # Last 10
            "stats": self.stats.to_dict(),
            "todos": [t.to_dict() for t in self.todos],
        }


@dataclass
class ConsoleState:
    """Complete console state for clients (web UI and future BLE)"""

    current_task: str | None = None
    pending_requests: list[PermissionRequest] = field(default_factory=list)
    completed_tasks: list[CompletedTask] = field(default_factory=list)
    stats: SessionStats = field(default_factory=SessionStats)
    yolo_mode: bool = False
    connected_clients: int = 0
    todos: list[TodoItem] = field(default_factory=list)

    # Multi-project support
    projects: dict[str, ProjectState] = field(default_factory=dict)
    active_project: str | None = None  # Currently selected project in UI

    # Claude Sessions tracking (session_id -> ClaudeSession)
    claude_sessions: dict[str, ClaudeSession] = field(default_factory=dict)
    active_session_id: str | None = None  # Currently active Claude session

    # Connection info (for future BLE support)
    web_clients: int = 0
    ble_connected: bool = False

    # Backward compatibility
    @property
    def pending_request(self) -> PermissionRequest | None:
        """Get the first pending request (for backward compatibility)"""
        return self.pending_requests[0] if self.pending_requests else None

    def get_project_state(self, project_path: str) -> ProjectState:
        """Get or create state for a project"""
        import os
        normalized = os.path.abspath(project_path)
        if normalized not in self.projects:
            self.projects[normalized] = ProjectState(project_path=normalized)
        return self.projects[normalized]

    def get_all_pending_requests(self) -> list[PermissionRequest]:
        """Get all pending requests across all projects"""
        requests = []
        for project in self.projects.values():
            requests.extend(project.pending_requests)
        return requests

    def get_project_list(self) -> list[dict[str, object]]:
        """Get list of all projects with summary info"""
        result = []
        for project in self.projects.values():
            result.append({
                "project_path": project.project_path,
                "project_name": project.project_name,
                "has_pending": len(project.pending_requests) > 0,
                "pending_count": len(project.pending_requests),
                "todo_count": len(project.todos),
                "stats": project.stats.to_dict(),
            })
        return result

    def get_session_list(self) -> list[dict[str, object]]:
        """Get list of all Claude sessions for UI tabs"""
        result = []
        for session in self.claude_sessions.values():
            session_dict = session.to_dict()
            # Add pending count for this session
            pending_count = sum(
                1 for r in self.pending_requests if r.session_id == session.session_id
            )
            session_dict["pending_count"] = pending_count
            result.append(session_dict)
        # Sort by start time (newest first)
        result.sort(key=lambda x: x["start_time"], reverse=True)
        return result

    def to_dict(self) -> dict[str, object]:
        return {
            "current_task": self.current_task,
            # For backward compatibility
            "pending_request": (
                self.pending_requests[0].to_display_dict() if self.pending_requests else None
            ),
            # New: all pending requests globally
            "pending_requests": [r.to_display_dict() for r in self.pending_requests],
            "completed_tasks": [
                t.to_dict() for t in self.completed_tasks[-10:]
            ],  # Last 10
            "stats": self.stats.to_dict(),
            "yolo_mode": self.yolo_mode,
            "connected_clients": self.connected_clients,
            "todos": [t.to_dict() for t in self.todos],
            # Multi-project support
            "projects": {k: v.to_dict() for k, v in self.projects.items()},
            "active_project": self.active_project,
            "project_list": self.get_project_list(),
            # Claude sessions (for UI tabs)
            "claude_sessions": {k: v.to_dict() for k, v in self.claude_sessions.items()},
            "session_list": self.get_session_list(),
            "active_session_id": self.active_session_id,
            # Extended info
            "web_clients": self.web_clients,
            "ble_connected": self.ble_connected,
        }

    def to_ble_bytes(self) -> bytes:
        """
        Serialize minimal state for Bluetooth transmission.

        For e-ink display: only essential info to minimize refresh.
        """
        data: dict[str, object] = {
            "task": (self.current_task or "")[:30],
            "pending": (
                self.pending_request.to_ble_bytes().decode()
                if self.pending_request
                else None
            ),
            "yolo": self.yolo_mode,
            "stats": {
                "total": self.stats.total_requests,
                "approved": self.stats.approved_count,
                "denied": self.stats.denied_count,
            },
            "todos": len(self.todos),
        }
        return json.dumps(data).encode("utf-8")
