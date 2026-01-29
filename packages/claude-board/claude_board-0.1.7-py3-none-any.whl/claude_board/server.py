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
import os
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import AppConfig
from .models import DecisionStatus, PermissionRequest
from .state import StateManager
from .types import DecisionInput, HookInput, TodoInput, YoloInput


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

    # === WebSocket Manager ===

    async def broadcast_state(state: dict[str, object]) -> None:
        """Broadcast state to all connected WebSocket clients"""
        if not connected_clients:
            return

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
        """Get current console state"""
        return state_manager.state.to_dict()

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

        if event in ["PreToolUse", "PermissionRequest"]:
            # Create a permission request
            request = PermissionRequest(
                tool_name=hook_input.tool_name,
                tool_input=dict(hook_input.tool_input),
                tool_use_id=hook_input.tool_use_id,
                session_id=hook_input.session_id,
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
            # Session ended
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
        """Update the TODO list"""
        todos_list = [
            {"content": t.content, "status": t.status, "activeForm": t.activeForm}
            for t in todo_input.todos
        ]
        await state_manager.update_todos(todos_list)
        return {"status": "ok", "count": len(todo_input.todos)}

    # === WebSocket Endpoint ===

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time updates"""
        await websocket.accept()
        connected_clients.append(websocket)
        await state_manager.update_web_client_count(len(connected_clients))

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

        try:
            while True:
                # Keep connection alive, handle any client messages
                _data = await websocket.receive_text()
                # Could handle client commands here if needed
        except WebSocketDisconnect:
            if websocket in connected_clients:
                connected_clients.remove(websocket)
            await state_manager.update_web_client_count(len(connected_clients))

    # === Static Files ===

    # Mount static files for CSS and JS
    web_dir = Path(__file__).parent / "web"
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=web_dir), name="static")

    # Store config and state_manager on app for access in CLI
    app.state.config = config
    app.state.state_manager = state_manager

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
