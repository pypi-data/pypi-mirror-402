"""
State Manager for Claude Board

Manages the console state and coordinates between:
- Hook scripts (via HTTP)
- Web clients (via WebSocket)
- Future: Bluetooth clients (via BLE GATT)

Uses asyncio.Future for blocking permission requests until
a decision is received from any connected client.

Supports multi-project state management where each project
maintains its own pending requests, todos, and statistics.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable
from datetime import datetime

from .models import (
    ClaudeSession,
    CompletedTask,
    ConsoleState,
    DecisionStatus,
    PermissionRequest,
    ProjectState,
    SessionStats,
    TodoItem,
    TodoStatus,
)


class StateManager:
    """
    Manages the console state and coordinates between
    hook scripts and clients (web/bluetooth).

    Thread-safe using asyncio.Lock.
    """

    def __init__(self, yolo_default: bool = False) -> None:
        self.state = ConsoleState(yolo_mode=yolo_default)
        self._pending_futures: dict[str, asyncio.Future[DecisionStatus]] = {}
        self._broadcast_callback: Callable[
            [dict[str, object]], Awaitable[None]
        ] | None = None
        self._ble_callback: Callable[[bytes], Awaitable[None]] | None = None
        self._lock = asyncio.Lock()

    def set_broadcast_callback(
        self, callback: Callable[[dict[str, object]], Awaitable[None]]
    ) -> None:
        """Set the callback for broadcasting state changes to WebSocket clients"""
        self._broadcast_callback = callback

    def set_ble_callback(
        self, callback: Callable[[bytes], Awaitable[None]]
    ) -> None:
        """Set the callback for sending state to Bluetooth client (future)"""
        self._ble_callback = callback

    async def _broadcast_state(self) -> None:
        """Broadcast current state to all connected clients"""
        # Web clients (WebSocket)
        if self._broadcast_callback:
            await self._broadcast_callback(self.state.to_dict())

        # Bluetooth client (future)
        if self._ble_callback and self.state.ble_connected:
            await self._ble_callback(self.state.to_ble_bytes())

    async def add_permission_request(
        self, request: PermissionRequest
    ) -> asyncio.Future[DecisionStatus]:
        """
        Add a new permission request and return a Future that will
        resolve when a decision is made.

        If YOLO mode is enabled, automatically approves.
        Multiple pending requests are now supported (from different sessions).

        The request is stored both in global state (for backward compatibility)
        and in the project-specific state (for multi-project support).
        """
        async with self._lock:
            # Get or create project state
            project_path = request.project_path or os.getcwd()
            project_state = self.state.get_project_state(project_path)

            # Add to project state's pending requests list
            project_state.pending_requests.append(request)
            project_state.stats.total_requests += 1

            # Also add to global state's pending requests list
            self.state.pending_requests.append(request)
            self.state.stats.total_requests += 1

            # Check YOLO mode - auto-approve ALL commands when enabled
            if self.state.yolo_mode:
                loop = asyncio.get_event_loop()
                future: asyncio.Future[DecisionStatus] = loop.create_future()
                future.set_result(DecisionStatus.APPROVED)
                await self._complete_request(request.id, DecisionStatus.APPROVED)
                return future

            # Create a future for the decision
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            self._pending_futures[request.id] = future

            await self._broadcast_state()
            return future

    async def make_decision(self, request_id: str, decision: DecisionStatus) -> bool:
        """
        Make a decision on a pending request.

        Can be called from:
        - Web UI (via HTTP API)
        - Bluetooth client (future, via BLE GATT)

        Returns True if the decision was applied.
        """
        async with self._lock:
            # Find the request in the pending list
            request = None
            for r in self.state.pending_requests:
                if r.id == request_id:
                    request = r
                    break

            if not request:
                return False

            # Resolve the future
            if request_id in self._pending_futures:
                future = self._pending_futures.pop(request_id)
                if not future.done():
                    future.set_result(decision)

            await self._complete_request(request_id, decision)
            return True

    async def _complete_request(
        self, request_id: str, decision: DecisionStatus
    ) -> None:
        """Move a request from pending to completed (in both global and project state)"""
        # Find and remove the request from global pending list
        request = None
        for r in self.state.pending_requests:
            if r.id == request_id:
                request = r
                self.state.pending_requests.remove(r)
                break

        if not request:
            return

        # Find and remove from project state
        project_state = None
        for ps in self.state.projects.values():
            for r in ps.pending_requests:
                if r.id == request_id:
                    ps.pending_requests.remove(r)
                    project_state = ps
                    break
            if project_state:
                break

        approved = decision == DecisionStatus.APPROVED

        completed = CompletedTask(
            id=request.id,
            tool_name=request.tool_name,
            display_text=request.get_display_text(),
            timestamp=datetime.now(),
            approved=approved,
            project_path=request.project_path,
        )

        # Update global state
        self.state.completed_tasks.append(completed)

        if approved:
            self.state.stats.approved_count += 1
        else:
            self.state.stats.denied_count += 1

        # Update project state
        if project_state:
            project_state.completed_tasks.append(completed)
            if approved:
                project_state.stats.approved_count += 1
            else:
                project_state.stats.denied_count += 1

        await self._broadcast_state()

    async def set_yolo_mode(self, enabled: bool) -> None:
        """Toggle YOLO (auto-approve) mode"""
        async with self._lock:
            self.state.yolo_mode = enabled
            await self._broadcast_state()

    async def set_current_task(self, task: str | None) -> None:
        """Update the current task description"""
        async with self._lock:
            self.state.current_task = task
            await self._broadcast_state()

    async def update_web_client_count(self, count: int) -> None:
        """Update the connected web client count"""
        self.state.web_clients = count
        self.state.connected_clients = count + (1 if self.state.ble_connected else 0)
        await self._broadcast_state()

    async def set_ble_connected(self, connected: bool) -> None:
        """Update Bluetooth connection status (future)"""
        async with self._lock:
            self.state.ble_connected = connected
            self.state.connected_clients = self.state.web_clients + (
                1 if connected else 0
            )
            await self._broadcast_state()

    async def reset_session(self) -> None:
        """Reset the session state"""
        async with self._lock:
            yolo = self.state.yolo_mode  # Preserve YOLO setting
            self.state = ConsoleState(yolo_mode=yolo)
            self._pending_futures.clear()
            await self._broadcast_state()

    async def update_todos(
        self, todos: list[dict[str, object]], project_path: str | None = None
    ) -> None:
        """Update the TODO list from Claude Code for a specific project"""
        async with self._lock:
            todo_items = [
                TodoItem(
                    content=str(t.get("content", "")),
                    status=TodoStatus(str(t.get("status", "pending"))),
                    active_form=str(t.get("activeForm", "")),
                    project_path=project_path or "",
                )
                for t in todos
            ]

            # Update global state (for backward compatibility)
            self.state.todos = todo_items

            # Update project-specific state
            if project_path:
                project_state = self.state.get_project_state(project_path)
                project_state.todos = todo_items

            await self._broadcast_state()

    async def set_active_project(self, project_path: str | None) -> None:
        """Set the currently active project in the UI"""
        async with self._lock:
            if project_path:
                # Normalize path
                self.state.active_project = os.path.abspath(project_path)
            else:
                self.state.active_project = None
            await self._broadcast_state()

    def get_project_state(self, project_path: str) -> ProjectState:
        """Get state for a specific project"""
        return self.state.get_project_state(project_path)

    def get_all_projects(self) -> list[ProjectState]:
        """Get all project states"""
        return list(self.state.projects.values())

    async def register_claude_session(
        self,
        session_id: str,
        project_path: str,
        chat_session_id: str | None = None,
        is_external: bool = True,
    ) -> ClaudeSession:
        """
        Register a new Claude Code session.

        Called when:
        - session_start_hook notifies us of a new external session
        - claude-board chat creates a new session (with chat_session_id linked)
        """
        async with self._lock:
            # Check if session already exists
            if session_id in self.state.claude_sessions:
                session = self.state.claude_sessions[session_id]
                # Update chat_session_id if provided
                if chat_session_id:
                    session.chat_session_id = chat_session_id
                    session.is_external = False
                return session

            # Create new session
            session = ClaudeSession(
                session_id=session_id,
                project_path=os.path.abspath(project_path),
                chat_session_id=chat_session_id,
                is_external=is_external,
            )
            self.state.claude_sessions[session_id] = session

            # Set as active session
            self.state.active_session_id = session_id

            # Also ensure project state exists
            self.state.get_project_state(project_path)

            await self._broadcast_state()
            return session

    async def set_active_session(self, session_id: str | None) -> None:
        """Set the currently active Claude session in the UI"""
        async with self._lock:
            self.state.active_session_id = session_id
            await self._broadcast_state()

    def get_claude_session(self, session_id: str) -> ClaudeSession | None:
        """Get a Claude session by ID"""
        return self.state.claude_sessions.get(session_id)

    async def handle_session_stop(
        self,
        session_id: str | None = None,
        project_path: str | None = None,
    ) -> None:
        """
        Handle session stop event from Claude Code.

        This is called when Claude finishes responding (Stop hook).
        We mark the session as ended, clear pending requests for this session,
        and notify clients so the UI can show that the session ended.
        """
        import logging
        logger = logging.getLogger(__name__)

        async with self._lock:
            logger.info(f"handle_session_stop called: session_id={session_id}, project_path={project_path}")
            logger.info(f"Current claude_sessions: {list(self.state.claude_sessions.keys())}")

            # Mark the Claude session as ended
            if session_id and session_id in self.state.claude_sessions:
                session = self.state.claude_sessions[session_id]
                session.ended = True
                session.end_time = datetime.now()
                logger.info(f"Marked session {session_id} as ended")
            elif session_id and project_path:
                # Session not found (e.g., server restarted) - create an ended session record
                # This allows the UI to show that a session ended even if we missed the start
                logger.info(f"Creating ended session record for {session_id}")
                session = ClaudeSession(
                    session_id=session_id,
                    project_path=os.path.abspath(project_path),
                    is_external=True,
                    ended=True,
                    end_time=datetime.now(),
                )
                self.state.claude_sessions[session_id] = session
                # Don't set as active since it's already ended
            else:
                logger.warning(f"Session {session_id} not found and no project_path provided")

            # Find and timeout pending requests from this session
            requests_to_timeout: list[str] = []

            for request in self.state.pending_requests:
                # Match by session_id if provided, otherwise match by project_path
                if session_id and request.session_id == session_id:
                    requests_to_timeout.append(request.id)
                elif project_path and request.project_path == project_path and not session_id:
                    requests_to_timeout.append(request.id)

            # Timeout matched requests
            for request_id in requests_to_timeout:
                if request_id in self._pending_futures:
                    future = self._pending_futures.pop(request_id)
                    if not future.done():
                        future.set_result(DecisionStatus.TIMEOUT)
                await self._complete_request(request_id, DecisionStatus.TIMEOUT)

            # Clear current task since Claude stopped
            self.state.current_task = None

            # Broadcast updated state to notify clients
            await self._broadcast_state()

    async def remove_claude_session(self, session_id: str) -> bool:
        """
        Remove a Claude session from tracking.

        This is typically called when user closes an ended session tab.
        Only allows removing sessions that have ended.

        Returns True if session was removed.
        """
        async with self._lock:
            if session_id not in self.state.claude_sessions:
                return False

            session = self.state.claude_sessions[session_id]

            # Only allow removing ended sessions
            if not session.ended:
                return False

            # Remove the session
            del self.state.claude_sessions[session_id]

            # If this was the active session, select another one
            if self.state.active_session_id == session_id:
                # Find another non-ended session, or the most recent ended one
                active_sessions = [
                    s for s in self.state.claude_sessions.values() if not s.ended
                ]
                if active_sessions:
                    self.state.active_session_id = active_sessions[0].session_id
                elif self.state.claude_sessions:
                    # Pick the first remaining session
                    self.state.active_session_id = next(
                        iter(self.state.claude_sessions.keys())
                    )
                else:
                    self.state.active_session_id = None

            await self._broadcast_state()
            return True
