"""
Type definitions for Claude Board

Uses Pydantic models for:
- API request/response schemas
- Hook input/output schemas
- Configuration validation
- Status reporting
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# Hook Input/Output Types
# ============================================================================


class HookToolInput(BaseModel):
    """Tool input from Claude Code hooks - flexible schema"""

    command: str | None = None  # Bash tool
    file_path: str | None = None  # Read/Write/Edit tools
    content: str | None = None  # Write tool
    old_string: str | None = None  # Edit tool
    new_string: str | None = None  # Edit tool
    pattern: str | None = None  # Glob/Grep tools
    description: str | None = None  # Bash tool description

    model_config = {"extra": "allow"}  # Allow additional fields


class HookInput(BaseModel):
    """Input received from Claude Code hooks via stdin"""

    session_id: str = ""
    hook_event_name: str = ""
    tool_name: str = ""
    tool_input: dict[str, object] = Field(default_factory=dict)
    tool_use_id: str = ""
    message: str = ""
    notification_type: str = ""
    cwd: str = ""
    transcript_path: str = ""
    permission_mode: str = ""

    model_config = {"extra": "allow"}


class PreToolUseDecision(BaseModel):
    """Decision output for PreToolUse hooks"""

    hookEventName: Literal["PreToolUse"] = "PreToolUse"
    permissionDecision: Literal["allow", "deny", "ask"] = "allow"
    permissionDecisionReason: str = ""
    updatedInput: dict[str, object] | None = None
    additionalContext: str | None = None


class PermissionRequestDecision(BaseModel):
    """Decision output for PermissionRequest hooks"""

    behavior: Literal["allow", "deny"]
    updatedInput: dict[str, object] | None = None
    message: str | None = None
    interrupt: bool | None = None


class PermissionRequestOutput(BaseModel):
    """Output for PermissionRequest hooks"""

    hookEventName: Literal["PermissionRequest"] = "PermissionRequest"
    decision: PermissionRequestDecision


class HookOutput(BaseModel):
    """Generic hook output wrapper"""

    hookSpecificOutput: PreToolUseDecision | PermissionRequestOutput | None = None
    continue_: bool | None = Field(default=None, alias="continue")
    stopReason: str | None = None
    suppressOutput: bool | None = None
    systemMessage: str | None = None

    model_config = {"populate_by_name": True}


# ============================================================================
# API Request/Response Types
# ============================================================================


class DecisionInput(BaseModel):
    """Input for approve/deny endpoints"""

    request_id: str


class YoloInput(BaseModel):
    """Input for YOLO mode toggle"""

    enabled: bool


class TodoItemInput(BaseModel):
    """Single TODO item from Claude Code"""

    content: str
    status: Literal["pending", "in_progress", "completed"]
    activeForm: str = ""


class TodoInput(BaseModel):
    """Input for TODO list update"""

    todos: list[TodoItemInput]


class HealthResponse(BaseModel):
    """Health check response"""

    status: Literal["ok", "error"]
    version: str
    connected_clients: int = 0
    ble_connected: bool = False
    yolo_mode: bool = False
    has_pending: bool = False


class StatusResponse(BaseModel):
    """Generic status response"""

    status: Literal["ok", "approved", "denied", "error"]
    message: str | None = None


# ============================================================================
# State Types (for WebSocket broadcast)
# ============================================================================


class PermissionRequestDisplay(BaseModel):
    """Permission request data for display"""

    id: str
    tool_name: str
    tool_input: dict[str, object]
    timestamp: str  # ISO format
    status: Literal["pending", "approved", "denied", "timeout"]
    display_text: str


class CompletedTaskDisplay(BaseModel):
    """Completed task data for display"""

    id: str
    tool_name: str
    display_text: str
    timestamp: str  # ISO format
    approved: bool


class TodoItemDisplay(BaseModel):
    """TODO item for display"""

    content: str
    status: Literal["pending", "in_progress", "completed"]
    activeForm: str


class SessionStatsDisplay(BaseModel):
    """Session statistics for display"""

    start_time: str  # ISO format
    elapsed_seconds: int
    total_requests: int
    approved_count: int
    denied_count: int


class ConsoleStateDisplay(BaseModel):
    """Complete console state for WebSocket broadcast"""

    current_task: str | None
    pending_request: PermissionRequestDisplay | None
    completed_tasks: list[CompletedTaskDisplay]
    stats: SessionStatsDisplay
    yolo_mode: bool
    connected_clients: int
    todos: list[TodoItemDisplay]
    web_clients: int
    ble_connected: bool


# ============================================================================
# Configuration Types
# ============================================================================


class ServerConfigModel(BaseModel):
    """Server configuration"""

    host: str = "0.0.0.0"
    port: int = 8765
    hook_timeout: int = 55


class HooksConfigModel(BaseModel):
    """Hooks behavior configuration"""

    safe_tools: list[str] = Field(
        default_factory=lambda: [
            "Glob",
            "Grep",
            "TodoWrite",
            "TodoRead",
            "Task",
            "WebSearch",
            "WebFetch",
        ]
    )
    dangerous_tools: list[str] = Field(
        default_factory=lambda: ["Write", "Edit", "Bash"]
    )
    safe_read_patterns: list[str] = Field(default_factory=lambda: ["."])


class BluetoothConfigModel(BaseModel):
    """Bluetooth configuration"""

    enabled: bool = False
    device_name: str = "Claude Board"
    auto_connect: bool = True
    service_uuid: str = "12345678-1234-5678-1234-56789abcdef0"


class AppConfigModel(BaseModel):
    """Main application configuration (Pydantic version)"""

    server: ServerConfigModel = Field(default_factory=ServerConfigModel)
    hooks: HooksConfigModel = Field(default_factory=HooksConfigModel)
    bluetooth: BluetoothConfigModel = Field(default_factory=BluetoothConfigModel)
    yolo_mode_default: bool = False


# ============================================================================
# Hook Status Types
# ============================================================================


class InstalledHookInfo(BaseModel):
    """Information about an installed hook"""

    event: str
    matcher: str


class HooksStatus(BaseModel):
    """Status of hooks installation"""

    installed: bool
    settings_file: str
    settings_exists: bool
    our_hooks: list[InstalledHookInfo]
    other_hooks_count: int


# ============================================================================
# RPC Types
# ============================================================================


class RPCRequest(BaseModel):
    """JSON-RPC 2.0 request"""

    jsonrpc: Literal["2.0"] = "2.0"
    method: str
    params: dict[str, object] = Field(default_factory=dict)
    id: int | str | None = None


class RPCError(BaseModel):
    """JSON-RPC 2.0 error"""

    code: int
    message: str
    data: object | None = None


class RPCResponse(BaseModel):
    """JSON-RPC 2.0 response"""

    jsonrpc: Literal["2.0"] = "2.0"
    result: object | None = None
    error: RPCError | None = None
    id: int | str | None = None


# ============================================================================
# WebSocket Message Types
# ============================================================================


class WebSocketMessage(BaseModel):
    """WebSocket message wrapper"""

    type: Literal["state_update", "notification", "error"]
    data: ConsoleStateDisplay | dict[str, object] | None = None
    timestamp: str  # ISO format
    message: str | None = None
