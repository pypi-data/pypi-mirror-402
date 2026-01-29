"""
State Manager for Claude Board

Manages the console state and coordinates between:
- Hook scripts (via HTTP)
- Web clients (via WebSocket)
- Future: Bluetooth clients (via BLE GATT)

Uses asyncio.Future for blocking permission requests until
a decision is received from any connected client.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime

from .models import (
    CompletedTask,
    ConsoleState,
    DecisionStatus,
    PermissionRequest,
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
        If there's already a pending request, auto-denies the old one.
        """
        async with self._lock:
            # If there's already a pending request, auto-deny it
            if self.state.pending_request:
                await self._complete_request(
                    self.state.pending_request.id, DecisionStatus.TIMEOUT
                )

            self.state.pending_request = request
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
            if not self.state.pending_request:
                return False

            if self.state.pending_request.id != request_id:
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
        """Move a request from pending to completed"""
        if not self.state.pending_request:
            return

        request = self.state.pending_request
        approved = decision == DecisionStatus.APPROVED

        completed = CompletedTask(
            id=request.id,
            tool_name=request.tool_name,
            display_text=request.get_display_text(),
            timestamp=datetime.now(),
            approved=approved,
        )

        self.state.completed_tasks.append(completed)
        self.state.pending_request = None

        if approved:
            self.state.stats.approved_count += 1
        else:
            self.state.stats.denied_count += 1

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

    async def update_todos(self, todos: list[dict[str, object]]) -> None:
        """Update the TODO list from Claude Code"""
        async with self._lock:
            self.state.todos = [
                TodoItem(
                    content=str(t.get("content", "")),
                    status=TodoStatus(str(t.get("status", "pending"))),
                    active_form=str(t.get("activeForm", "")),
                )
                for t in todos
            ]
            await self._broadcast_state()
