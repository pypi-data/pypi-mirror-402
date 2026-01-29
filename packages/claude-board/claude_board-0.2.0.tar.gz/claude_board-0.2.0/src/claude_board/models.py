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
    timestamp: datetime = field(default_factory=datetime.now)
    status: DecisionStatus = DecisionStatus.PENDING

    def to_display_dict(self) -> dict[str, object]:
        """Convert to frontend-friendly format"""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "display_text": self.get_display_text(),
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

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "display_text": self.display_text,
            "timestamp": self.timestamp.isoformat(),
            "approved": self.approved,
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

    def to_dict(self) -> dict[str, object]:
        return {
            "content": self.content,
            "status": self.status.value,
            "activeForm": self.active_form,
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
class ConsoleState:
    """Complete console state for clients (web UI and future BLE)"""

    current_task: str | None = None
    pending_request: PermissionRequest | None = None
    completed_tasks: list[CompletedTask] = field(default_factory=list)
    stats: SessionStats = field(default_factory=SessionStats)
    yolo_mode: bool = False
    connected_clients: int = 0
    todos: list[TodoItem] = field(default_factory=list)

    # Connection info (for future BLE support)
    web_clients: int = 0
    ble_connected: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "current_task": self.current_task,
            "pending_request": (
                self.pending_request.to_display_dict() if self.pending_request else None
            ),
            "completed_tasks": [
                t.to_dict() for t in self.completed_tasks[-10:]
            ],  # Last 10
            "stats": self.stats.to_dict(),
            "yolo_mode": self.yolo_mode,
            "connected_clients": self.connected_clients,
            "todos": [t.to_dict() for t in self.todos],
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
