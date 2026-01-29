"""
Claude Board Web Server

FastAPI-based server that:
1. Receives hook events from Claude Code
2. Serves a web UI for approving/denying requests
3. Uses WebSocket for real-time updates
4. Provides Unix socket RPC API for GUI tools
5. Future: Coordinates with Bluetooth clients
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .chat.session import ChatSessionManager
from .config import AppConfig
from .models import DecisionStatus, PermissionRequest
from .state import StateManager
from .types import DecisionInput, HookInput, TodoInput, YoloInput

# Set up module logger
logger = logging.getLogger(__name__)


class RPCServer:
    """
    Unix socket RPC server for programmatic control.

    Protocol: JSON-RPC 2.0 over Unix domain socket.
    Each message is newline-delimited JSON.

    Available methods:
    - get_state: Get current console state
    - approve: Approve a pending request
    - deny: Deny a pending request
    - set_yolo: Set YOLO mode
    - reset: Reset session
    - get_todos: Get TODO list
    - health: Health check

    Example request:
    {"jsonrpc": "2.0", "method": "get_state", "id": 1}

    Example response:
    {"jsonrpc": "2.0", "result": {...}, "id": 1}
    """

    def __init__(self, socket_path: Path, state_manager: StateManager) -> None:
        self.socket_path = socket_path
        self.state_manager = state_manager
        self.server: asyncio.Server | None = None
        self._handlers: dict[str, Callable[[dict[str, object]], Awaitable[dict[str, object]]]] = {}
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Register RPC method handlers"""
        self._handlers = {
            "get_state": self._handle_get_state,
            "approve": self._handle_approve,
            "deny": self._handle_deny,
            "set_yolo": self._handle_set_yolo,
            "reset": self._handle_reset,
            "get_todos": self._handle_get_todos,
            "health": self._handle_health,
            "subscribe": self._handle_subscribe,
        }

    async def _handle_get_state(self, params: dict[str, object]) -> dict[str, object]:
        """Get current console state"""
        return self.state_manager.state.to_dict()

    async def _handle_approve(self, params: dict[str, object]) -> dict[str, object]:
        """Approve a pending request"""
        request_id = params.get("request_id")
        if not request_id or not isinstance(request_id, str):
            raise ValueError("request_id is required")
        success = await self.state_manager.make_decision(request_id, DecisionStatus.APPROVED)
        return {"success": success}

    async def _handle_deny(self, params: dict[str, object]) -> dict[str, object]:
        """Deny a pending request"""
        request_id = params.get("request_id")
        if not request_id or not isinstance(request_id, str):
            raise ValueError("request_id is required")
        success = await self.state_manager.make_decision(request_id, DecisionStatus.DENIED)
        return {"success": success}

    async def _handle_set_yolo(self, params: dict[str, object]) -> dict[str, object]:
        """Set YOLO mode"""
        enabled = bool(params.get("enabled", False))
        await self.state_manager.set_yolo_mode(enabled)
        return {"yolo_mode": enabled}

    async def _handle_reset(self, params: dict[str, object]) -> dict[str, object]:
        """Reset session"""
        await self.state_manager.reset_session()
        return {"success": True}

    async def _handle_get_todos(self, params: dict[str, object]) -> dict[str, object]:
        """Get TODO list"""
        return {"todos": [t.to_dict() for t in self.state_manager.state.todos]}

    async def _handle_health(self, params: dict[str, object]) -> dict[str, object]:
        """Health check"""
        return {
            "status": "ok",
            "version": "0.1.0",
            "yolo_mode": self.state_manager.state.yolo_mode,
            "has_pending": self.state_manager.state.pending_request is not None,
        }

    async def _handle_subscribe(self, params: dict[str, object]) -> dict[str, object]:
        """Subscribe to state updates (returns current state, client should keep connection open)"""
        return self.state_manager.state.to_dict()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle a connected RPC client"""
        _peer = writer.get_extra_info("peername")
        _subscribe_mode = False

        try:
            while True:
                # Read a line (newline-delimited JSON)
                data = await reader.readline()
                if not data:
                    break

                try:
                    request: dict[str, object] = json.loads(data.decode("utf-8"))
                except json.JSONDecodeError as e:
                    response: dict[str, object] = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": f"Parse error: {e}"},
                        "id": None,
                    }
                    writer.write((json.dumps(response) + "\n").encode("utf-8"))
                    await writer.drain()
                    continue

                # Validate JSON-RPC request
                request_id = request.get("id")
                method = request.get("method")
                params_raw = request.get("params", {})
                params: dict[str, object] = (
                    params_raw if isinstance(params_raw, dict) else {}
                )

                if not method or not isinstance(method, str):
                    response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "Invalid request: method is required",
                        },
                        "id": request_id,
                    }
                else:
                    handler = self._handlers.get(method)
                    if not handler:
                        response = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {method}",
                            },
                            "id": request_id,
                        }
                    else:
                        try:
                            result = await handler(params)
                            response = {
                                "jsonrpc": "2.0",
                                "result": result,
                                "id": request_id,
                            }

                            # If subscribing, enter subscription mode
                            if method == "subscribe":
                                _subscribe_mode = True
                        except Exception as e:
                            response = {
                                "jsonrpc": "2.0",
                                "error": {"code": -32000, "message": str(e)},
                                "id": request_id,
                            }

                writer.write((json.dumps(response) + "\n").encode("utf-8"))
                await writer.drain()

        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def start(self) -> None:
        """Start the RPC server"""
        # Ensure parent directory exists
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing socket file
        if self.socket_path.exists():
            self.socket_path.unlink()

        self.server = await asyncio.start_unix_server(
            self._handle_client, path=str(self.socket_path)
        )

        # Set socket permissions (readable/writable by owner only)
        os.chmod(self.socket_path, 0o600)

    async def stop(self) -> None:
        """Stop the RPC server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Clean up socket file
        if self.socket_path.exists():
            self.socket_path.unlink()


def create_app(config: AppConfig | None = None) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        config: Application configuration. Uses defaults if not provided.

    Returns:
        Configured FastAPI application.
    """
    if config is None:
        config = AppConfig()

    app = FastAPI(
        title="Claude Board",
        description="Permission approval console for Claude Code",
        version="0.1.0",
    )

    # State manager
    state_manager = StateManager(yolo_default=config.yolo_mode_default)
    connected_clients: list[WebSocket] = []

    # Session manager for chat sessions
    session_manager = ChatSessionManager()

    # === WebSocket Manager ===

    async def broadcast_state(state: dict[str, object]) -> None:
        """Broadcast state to all connected WebSocket clients"""
        if not connected_clients:
            return

        # Inject chat_sessions into state for WebSocket push
        # This avoids the need for separate /api/sessions polling
        state["chat_sessions"] = session_manager.list_sessions()

        message = json.dumps(
            {"type": "state_update", "data": state, "timestamp": datetime.now().isoformat()}
        )

        # Send to all clients, remove disconnected ones
        disconnected: list[WebSocket] = []
        for client in connected_clients:
            try:
                await client.send_text(message)
            except Exception:
                disconnected.append(client)

        for client in disconnected:
            if client in connected_clients:
                connected_clients.remove(client)

    # Set up state manager callback
    state_manager.set_broadcast_callback(broadcast_state)

    # === HTTP Endpoints ===

    @app.get("/")
    async def root() -> FileResponse:
        """Serve the main web UI"""
        web_dir = Path(__file__).parent / "web"
        html_path = web_dir / "index.html"
        return FileResponse(html_path)

    @app.get("/api/state")
    async def get_state() -> dict[str, object]:
        """Get current console state (including chat_sessions)"""
        state = state_manager.state.to_dict()
        # Include chat_sessions for consistency with WebSocket push
        state["chat_sessions"] = session_manager.list_sessions()
        return state

    @app.get("/api/health")
    async def health_check() -> dict[str, object]:
        """Health check endpoint"""
        return {
            "status": "ok",
            "version": "0.1.0",
            "connected_clients": len(connected_clients),
            "ble_connected": state_manager.state.ble_connected,
        }

    @app.post("/api/hook")
    async def handle_hook(hook_input: HookInput) -> dict[str, object]:
        """
        Handle incoming hook events from Claude Code.

        For PreToolUse/PermissionRequest hooks, this blocks until a decision
        is made or timeout occurs.
        """
        event = hook_input.hook_event_name

        # Get project path from hook input
        project_path = hook_input.project_path or hook_input.cwd or ""

        if event in ["PreToolUse", "PermissionRequest"]:
            # Auto-register session if not already registered
            # This handles the case where permission hook fires before SessionStart hook
            if hook_input.session_id and project_path:
                if hook_input.session_id not in state_manager.state.claude_sessions:
                    await state_manager.register_claude_session(
                        session_id=hook_input.session_id,
                        project_path=project_path,
                        is_external=True,
                    )

            # Create a permission request
            request = PermissionRequest(
                tool_name=hook_input.tool_name,
                tool_input=dict(hook_input.tool_input),
                tool_use_id=hook_input.tool_use_id,
                session_id=hook_input.session_id,
                project_path=project_path,
            )

            # Add to state and get a future for the decision
            decision_future = await state_manager.add_permission_request(request)

            try:
                # Wait for decision with timeout
                decision = await asyncio.wait_for(
                    decision_future, timeout=config.server.hook_timeout
                )
            except asyncio.TimeoutError:
                decision = DecisionStatus.TIMEOUT
                await state_manager.make_decision(request.id, DecisionStatus.TIMEOUT)

            # Return the decision in hook-compatible format
            if event == "PreToolUse":
                # PreToolUse format
                if decision == DecisionStatus.APPROVED:
                    return {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "allow",
                            "permissionDecisionReason": "Approved by Claude Board",
                        }
                    }
                else:
                    return {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": f"Denied by Claude Board ({decision.value})",
                        }
                    }
            else:
                # PermissionRequest format
                if decision == DecisionStatus.APPROVED:
                    return {
                        "hookSpecificOutput": {
                            "hookEventName": "PermissionRequest",
                            "decision": {"behavior": "allow"},
                        }
                    }
                else:
                    return {
                        "hookSpecificOutput": {
                            "hookEventName": "PermissionRequest",
                            "decision": {
                                "behavior": "deny",
                                "message": f"Denied by Claude Board ({decision.value})",
                            },
                        }
                    }

        elif event == "Notification":
            # Just broadcast the notification, don't block
            return {"status": "ok"}

        elif event == "Stop":
            # Claude finished responding to ONE message (fires after each response)
            # This does NOT mean the session ended - user can send more messages
            # We should NOT mark the session as ended here!
            #
            # Stop hook is useful for:
            # 1. Knowing Claude is now idle/waiting for input
            # 2. Optionally blocking to make Claude continue working
            #
            # Notify frontend that Claude finished responding (single notification)
            logger.info(
                f"Stop event received for session {hook_input.session_id} "
                f"(Claude finished responding, session still active)"
            )

            # Broadcast stop notification to all WebSocket clients
            stop_message = json.dumps({
                "type": "stop_notification",
                "session_id": hook_input.session_id,
                "project_path": project_path,
                "timestamp": datetime.now().isoformat(),
            })
            disconnected: list[WebSocket] = []
            for client in connected_clients:
                try:
                    await client.send_text(stop_message)
                except Exception:
                    disconnected.append(client)
            for client in disconnected:
                if client in connected_clients:
                    connected_clients.remove(client)

            return {"status": "ok"}

        elif event == "SessionEnd":
            # Session ended (more reliable - includes Ctrl+C, /clear, logout, etc.)
            await state_manager.handle_session_stop(
                session_id=hook_input.session_id,
                project_path=project_path,
            )
            return {"status": "ok"}

        return {"status": "ok"}

    @app.post("/api/approve")
    async def approve_request(decision_input: DecisionInput) -> dict[str, str]:
        """Approve a pending permission request"""
        success = await state_manager.make_decision(
            decision_input.request_id, DecisionStatus.APPROVED
        )
        if not success:
            raise HTTPException(
                status_code=404, detail="Request not found or already decided"
            )
        return {"status": "approved"}

    @app.post("/api/deny")
    async def deny_request(decision_input: DecisionInput) -> dict[str, str]:
        """Deny a pending permission request"""
        success = await state_manager.make_decision(
            decision_input.request_id, DecisionStatus.DENIED
        )
        if not success:
            raise HTTPException(
                status_code=404, detail="Request not found or already decided"
            )
        return {"status": "denied"}

    @app.post("/api/yolo")
    async def toggle_yolo(yolo_input: YoloInput) -> dict[str, object]:
        """Toggle YOLO (auto-approve) mode"""
        await state_manager.set_yolo_mode(yolo_input.enabled)
        return {"status": "ok", "yolo_mode": yolo_input.enabled}

    @app.post("/api/reset")
    async def reset_session() -> dict[str, str]:
        """Reset the session state"""
        await state_manager.reset_session()
        return {"status": "ok"}

    @app.post("/api/todos")
    async def update_todos(todo_input: TodoInput) -> dict[str, object]:
        """Update the TODO list for a specific project"""
        # Auto-register session if session_id is provided but not registered yet
        # This handles the case where TODO hook fires before SessionStart hook
        if todo_input.session_id and todo_input.project_path:
            if todo_input.session_id not in state_manager.state.claude_sessions:
                await state_manager.register_claude_session(
                    session_id=todo_input.session_id,
                    project_path=todo_input.project_path,
                    is_external=True,  # Assume external since we didn't get SessionStart
                )

        todos_list = [
            {"content": t.content, "status": t.status, "activeForm": t.activeForm}
            for t in todo_input.todos
        ]
        await state_manager.update_todos(todos_list, project_path=todo_input.project_path)
        return {"status": "ok", "count": len(todo_input.todos)}

    # === Multi-project API ===

    @app.get("/api/projects")
    async def list_projects() -> dict[str, object]:
        """List all projects with their states"""
        return {
            "projects": state_manager.state.get_project_list(),
            "active_project": state_manager.state.active_project,
        }

    @app.get("/api/projects/{project_path:path}")
    async def get_project_state(project_path: str) -> dict[str, object]:
        """Get state for a specific project"""
        import urllib.parse
        decoded_path = urllib.parse.unquote(project_path)
        project_state = state_manager.get_project_state(decoded_path)
        return project_state.to_dict()

    @app.post("/api/projects/active")
    async def set_active_project(data: dict[str, str | None]) -> dict[str, object]:
        """Set the active project for UI display"""
        project_path = data.get("project_path")
        await state_manager.set_active_project(project_path)
        return {"status": "ok", "active_project": state_manager.state.active_project}

    @app.post("/api/session/notify")
    async def session_notify(data: dict[str, str | None]) -> dict[str, str]:
        """
        Receive session lifecycle notifications from hooks.

        Called by session_start_hook.py when a new Claude Code session starts.
        The hook may pass a chat_session_id (from CLAUDE_BOARD_SESSION_ID env var)
        if this Claude session was started by claude-board chat.
        """
        event = data.get("event", "unknown")
        session_id = data.get("session_id", "unknown")
        project_path = data.get("project_path", "")
        chat_session_id = data.get("chat_session_id")  # From CLAUDE_BOARD_SESSION_ID env

        if event == "session_start":
            # Check if this session was started by claude-board chat
            is_external = True
            if chat_session_id:
                # Link to the chat session if it exists
                chat_session = session_manager.get_session(chat_session_id)
                if chat_session:
                    # Update the chat session's claude_session_id
                    chat_session.claude_session_id = session_id
                    is_external = False  # Not external, it's managed by us

            # Register the Claude session (creates tab immediately)
            if session_id and project_path:
                await state_manager.register_claude_session(
                    session_id=session_id,
                    project_path=project_path,
                    chat_session_id=chat_session_id,
                    is_external=is_external,
                )
            elif project_path:
                # Fallback: just set active project
                await state_manager.set_active_project(project_path)

        return {"status": "ok", "event": event, "session_id": session_id}

    @app.post("/api/session/active")
    async def set_active_session(data: dict[str, str]) -> dict[str, str]:
        """Set the active Claude session for UI"""
        session_id = data.get("session_id")
        await state_manager.set_active_session(session_id)
        return {"status": "ok", "active_session_id": session_id}

    @app.delete("/api/session/{session_id}")
    async def remove_session(session_id: str) -> dict[str, str]:
        """Remove an ended Claude session from tracking"""
        success = await state_manager.remove_claude_session(session_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Session not found or not ended yet"
            )
        return {"status": "ok"}

    # === Session API ===

    @app.get("/api/sessions")
    async def list_sessions() -> dict[str, object]:
        """List all chat sessions"""
        # Clean up dead sessions first
        session_manager.cleanup_dead_sessions()
        return {"sessions": session_manager.list_sessions()}

    @app.post("/api/sessions")
    async def create_session(data: dict[str, object]) -> dict[str, object]:
        """
        Create a new chat session.

        This endpoint allows external processes (like claude-board chat CLI)
        to create sessions that are managed by the server process.

        Request body:
        - name: Optional friendly name for the session
        - project_path: Project directory (defaults to server's cwd)
        - resume: Resume option (true for picker, string for specific session ID)
        - claude_args: Additional arguments to pass to claude CLI
        """
        name = data.get("name")
        project_path = data.get("project_path", os.getcwd())
        resume = data.get("resume")
        claude_args = data.get("claude_args")

        # Convert resume to proper type
        resume_option: str | bool | None = None
        if resume is True:
            resume_option = True
        elif isinstance(resume, str) and resume:
            resume_option = resume

        try:
            session = await session_manager.create_session(
                name=str(name) if name else None,
                project_path=str(project_path),
                resume=resume_option,
                claude_args=list(claude_args) if claude_args else None,
            )
            return {"status": "ok", "session": session.to_dict()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str) -> dict[str, object]:
        """Get a specific session"""
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session.to_dict()

    @app.post("/api/sessions/{session_id}/prompt")
    async def send_session_prompt(session_id: str, data: dict[str, str]) -> dict[str, str]:
        """Send a prompt to a session"""
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if not session.is_alive():
            raise HTTPException(status_code=400, detail="Session is not running")

        prompt = data.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        await session.send_prompt(prompt, source="web")
        return {"status": "ok"}

    @app.post("/api/sessions/{session_id}/input")
    async def send_session_input(session_id: str, data: dict[str, str]) -> dict[str, str]:
        """Send raw input to a session"""
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if not session.is_alive():
            raise HTTPException(status_code=400, detail="Session is not running")

        input_data = data.get("data", "")
        if not input_data:
            raise HTTPException(status_code=400, detail="Data is required")

        await session.send_input(input_data.encode("utf-8"), source="web")
        return {"status": "ok"}

    @app.delete("/api/sessions/{session_id}")
    async def stop_session(session_id: str) -> dict[str, str]:
        """Stop a session"""
        success = await session_manager.stop_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "ok"}

    # === WebSocket Endpoint ===

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time updates"""
        await websocket.accept()
        connected_clients.append(websocket)
        await state_manager.update_web_client_count(len(connected_clients))

        try:
            # Send initial state
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "state_update",
                        "data": state_manager.state.to_dict(),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

            while True:
                # Keep connection alive, handle any client messages
                _data = await websocket.receive_text()
                # Could handle client commands here if needed
        except WebSocketDisconnect:
            pass
        except Exception as e:
            # Handle other connection errors (e.g., connection reset)
            logger.debug(f"WebSocket error: {e}")
        finally:
            if websocket in connected_clients:
                connected_clients.remove(websocket)
            await state_manager.update_web_client_count(len(connected_clients))

    # === Session Terminal WebSocket ===

    @app.websocket("/ws/sessions/{session_id}/terminal")
    async def session_terminal_websocket(websocket: WebSocket, session_id: str) -> None:
        """WebSocket endpoint for terminal output streaming"""
        session = session_manager.get_session(session_id)
        if not session:
            await websocket.close(code=4004, reason="Session not found")
            return

        await websocket.accept()

        # Callback to send output to this websocket
        async def output_callback(data: bytes) -> None:
            try:
                await websocket.send_json({
                    "type": "output",
                    "data": data.decode("utf-8", errors="replace")
                })
            except WebSocketDisconnect:
                pass
            except Exception:
                pass

        # Attach callback and get history
        # Note: attach_web_callback gets history snapshot BEFORE registering callback
        # to avoid duplicates (at the cost of potentially missing a tiny bit of output)
        try:
            history = await session.attach_web_callback(output_callback)

            # Send history
            if history:
                await websocket.send_json({
                    "type": "history",
                    "data": history.decode("utf-8", errors="replace")
                })

            # Handle incoming messages
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type", "")

                if msg_type == "input":
                    # Forward input to session
                    input_data = data.get("data", "")
                    if input_data:
                        await session.send_input(input_data.encode("utf-8"), source="web")
                elif msg_type == "resize":
                    # Handle terminal resize
                    rows = data.get("rows", 24)
                    cols = data.get("cols", 80)
                    session.resize(rows, cols)
                elif msg_type == "prompt":
                    # Send a prompt
                    prompt = data.get("prompt", "")
                    if prompt:
                        await session.send_prompt(prompt, source="web")

        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.debug(f"Terminal WebSocket error: {e}")

        finally:
            # Detach callback
            session.detach_web_callback(output_callback)

            # Notify if session ended
            if not session.is_alive():
                try:
                    await websocket.send_json({"type": "session_ended"})
                except Exception:
                    pass

    # === Static Files ===

    # Mount static files for CSS and JS
    web_dir = Path(__file__).parent / "web"
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=web_dir), name="static")

    # Store config, state_manager, and session_manager on app for access in CLI
    app.state.config = config
    app.state.state_manager = state_manager
    app.state.session_manager = session_manager

    return app


def run_server(
    host: str = "0.0.0.0",
    port: int = 8765,
    config: AppConfig | None = None,
    socket_path: Path | None = None,
) -> None:
    """
    Run the server (blocking).

    Args:
        host: Host to bind to.
        port: Port to listen on.
        config: Application configuration.
        socket_path: Path for Unix socket RPC API (optional).
    """
    import uvicorn

    if config is None:
        config = AppConfig()
        config.server.host = host
        config.server.port = port

    app = create_app(config)

    # If socket_path is provided, run with RPC server
    if socket_path:

        async def run_with_rpc() -> None:
            # Create RPC server
            rpc_server = RPCServer(socket_path, app.state.state_manager)
            await rpc_server.start()

            # Create uvicorn config
            uvi_config = uvicorn.Config(
                app,
                host=config.server.host,
                port=config.server.port,
                log_level="info",
            )
            server = uvicorn.Server(uvi_config)

            try:
                await server.serve()
            finally:
                await rpc_server.stop()

        asyncio.run(run_with_rpc())
    else:
        uvicorn.run(app, host=config.server.host, port=config.server.port)
