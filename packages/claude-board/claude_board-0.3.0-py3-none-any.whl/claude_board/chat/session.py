"""
PTY Session Management for Claude Code

Provides persistent Claude Code sessions that can be:
- Run in background (daemon mode)
- Attached/detached from terminals
- Controlled via Web UI
- Associated with specific projects
"""

from __future__ import annotations

import asyncio
import fcntl
import os
import pty
import shutil
import struct
import subprocess
import sys
import termios
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from collections.abc import Awaitable


class SessionState(str, Enum):
    """State of a chat session"""
    STARTING = "starting"
    RUNNING = "running"
    IDLE = "idle"  # Claude is waiting for input
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ChatSession:
    """
    A persistent Claude Code chat session.

    Features:
    - PTY-based process management
    - Output buffering for late-joining clients
    - Multi-client support (terminal + web)
    - Project association
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str | None = None
    project_path: str = ""  # The project directory this session is associated with

    # PTY state
    pty_master_fd: int = -1
    process: subprocess.Popen | None = None

    # Claude Code session info (from hooks)
    claude_session_id: str | None = None

    # Output buffer for late-joining clients
    # maxlen limits total chunks, not bytes - each chunk is up to 4096 bytes
    output_buffer: deque[bytes] = field(default_factory=lambda: deque(maxlen=200))
    _total_output_bytes: int = 0

    # Connected clients
    terminal_write_fds: list[int] = field(default_factory=list)
    web_callbacks: list[Callable[[bytes], Awaitable[None]]] = field(default_factory=list)

    # State
    state: SessionState = SessionState.STARTING
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    # Output reader task
    _reader_task: asyncio.Task | None = None

    def __post_init__(self) -> None:
        if not self.project_path:
            self.project_path = os.getcwd()

    @property
    def project_name(self) -> str:
        """Get a display name for the project"""
        return Path(self.project_path).name

    async def start(
        self,
        resume: str | bool | None = None,
        claude_args: list[str] | None = None,
    ) -> None:
        """
        Start the Claude Code process with a PTY.

        Args:
            resume: True for interactive resume picker, string for specific session ID
            claude_args: Additional arguments to pass to claude
        """
        # Find claude executable
        claude_path = shutil.which("claude")
        if not claude_path:
            raise RuntimeError("Claude Code CLI not found in PATH")

        # Create PTY
        master_fd, slave_fd = pty.openpty()
        self.pty_master_fd = master_fd

        # Build command
        cmd = [claude_path]
        if resume is True:
            cmd.append("--resume")
        elif isinstance(resume, str) and resume:
            cmd.extend(["--resume", resume])

        if claude_args:
            cmd.extend(claude_args)

        # Set initial terminal size
        try:
            # Default to 80x24 if we can't get terminal size
            rows, cols = 24, 80
            if sys.stdout.isatty():
                size = os.get_terminal_size()
                rows, cols = size.lines, size.columns
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)
        except (OSError, ValueError):
            pass

        # Start process
        self.process = subprocess.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=self.project_path,
            start_new_session=True,
            env={
                **os.environ,
                "CLAUDE_BOARD_SESSION_ID": self.session_id,
            },
        )

        # Close slave fd in parent (child has its own copy)
        os.close(slave_fd)

        self.state = SessionState.RUNNING
        self.last_activity = datetime.now()

        # Start output reader
        self._reader_task = asyncio.create_task(self._read_output_loop())

    async def _read_output_loop(self) -> None:
        """Continuously read PTY output and forward to clients"""
        loop = asyncio.get_event_loop()

        while self.process and self.process.poll() is None:
            try:
                # Read from PTY (non-blocking via executor)
                data = await loop.run_in_executor(
                    None,
                    lambda: os.read(self.pty_master_fd, 4096)
                )

                if not data:
                    break

                self.last_activity = datetime.now()
                self._total_output_bytes += len(data)

                # Store in buffer
                self.output_buffer.append(data)

                # Forward to terminal clients
                disconnected_terminals: list[int] = []
                for fd in self.terminal_write_fds:
                    try:
                        os.write(fd, data)
                    except OSError:
                        disconnected_terminals.append(fd)

                for fd in disconnected_terminals:
                    self.terminal_write_fds.remove(fd)

                # Forward to web clients
                disconnected_web: list[Callable[[bytes], Awaitable[None]]] = []
                for callback in self.web_callbacks:
                    try:
                        await callback(data)
                    except Exception:
                        disconnected_web.append(callback)

                for callback in disconnected_web:
                    if callback in self.web_callbacks:
                        self.web_callbacks.remove(callback)

            except OSError:
                break
            except asyncio.CancelledError:
                break

        self.state = SessionState.STOPPED

    async def send_input(self, data: bytes, source: str = "unknown") -> None:
        """
        Send input to Claude Code.

        Args:
            data: Raw bytes to send (including newline if needed)
            source: "terminal" or "web" for logging
        """
        if self.pty_master_fd < 0:
            raise RuntimeError("Session not started")

        os.write(self.pty_master_fd, data)
        self.last_activity = datetime.now()

    async def send_prompt(self, prompt: str, source: str = "web") -> None:
        """
        Send a text prompt to Claude Code.

        Claude Code uses ink (React for CLI) which processes input via useInput hook.
        When text is sent as a single chunk, ink treats it as "pasted text" and
        the entire string (including \\r) is passed to the input handler as one unit.

        To properly trigger submission, we must:
        1. Send the prompt text first
        2. Wait a brief moment for ink's event loop to process it
        3. Send CR (\\r) separately to trigger the 'return' key detection

        Args:
            prompt: The prompt text
            source: Source identifier
        """
        if self.pty_master_fd < 0:
            raise RuntimeError("Session not started")

        # Send the prompt text first
        if prompt:
            await self.send_input(prompt.encode("utf-8"), source)
            # Small delay to let ink process the text input
            await asyncio.sleep(0.05)

        # Send CR separately to trigger submission
        # ink's parseKeypress identifies '\r' as 'return' key
        await self.send_input(b"\r", source)

    def attach_terminal(self, write_fd: int) -> bytes:
        """
        Attach a terminal for output.

        Args:
            write_fd: File descriptor to write output to

        Returns:
            Buffered output for replay
        """
        if write_fd not in self.terminal_write_fds:
            self.terminal_write_fds.append(write_fd)

        # Return buffered output
        return b"".join(self.output_buffer)

    def detach_terminal(self, write_fd: int) -> None:
        """Detach a terminal from output"""
        if write_fd in self.terminal_write_fds:
            self.terminal_write_fds.remove(write_fd)

    async def attach_web_callback(
        self, callback: Callable[[bytes], Awaitable[None]]
    ) -> bytes:
        """
        Attach a web client callback for output.

        IMPORTANT: We get history snapshot FIRST, then register callback.
        This means there might be a small window where output is missed,
        but it avoids the bigger problem of duplicated content.

        The server-side buffering ensures correct ordering of outputs.

        Args:
            callback: Async function to call with output data

        Returns:
            Buffered output for replay
        """
        # Get history snapshot FIRST
        history = b"".join(self.output_buffer)

        # Then register callback
        # Any output between snapshot and registration will be in the next chunk
        # but won't be duplicated
        if callback not in self.web_callbacks:
            self.web_callbacks.append(callback)

        return history

    def detach_web_callback(
        self, callback: Callable[[bytes], Awaitable[None]]
    ) -> None:
        """Detach a web client callback"""
        if callback in self.web_callbacks:
            self.web_callbacks.remove(callback)

    def resize(self, rows: int, cols: int) -> None:
        """Resize the PTY"""
        if self.pty_master_fd < 0:
            return

        try:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.pty_master_fd, termios.TIOCSWINSZ, winsize)
        except OSError:
            pass

    async def stop(self, force: bool = False) -> None:
        """
        Stop the session.

        Args:
            force: If True, use SIGKILL instead of SIGTERM
        """
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        if self.process:
            import signal
            sig = signal.SIGKILL if force else signal.SIGTERM
            try:
                self.process.send_signal(sig)
                self.process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if not force:
                    self.process.kill()

        if self.pty_master_fd >= 0:
            try:
                os.close(self.pty_master_fd)
            except OSError:
                pass
            self.pty_master_fd = -1

        self.state = SessionState.STOPPED

    def is_alive(self) -> bool:
        """Check if the session is still running"""
        if self.process is None:
            return False
        return self.process.poll() is None

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary for API responses"""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "project_path": self.project_path,
            "project_name": self.project_name,
            "claude_session_id": self.claude_session_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "terminal_clients": len(self.terminal_write_fds),
            "web_clients": len(self.web_callbacks),
            "output_bytes": self._total_output_bytes,
            "is_alive": self.is_alive(),
        }


class ChatSessionManager:
    """
    Manages multiple chat sessions.

    Features:
    - Session lifecycle management
    - Project-based session lookup
    - Persistence (save/load session metadata)
    """

    def __init__(self, state_dir: Path | None = None) -> None:
        self.sessions: dict[str, ChatSession] = {}
        self.state_dir = state_dir or (Path.home() / ".claude-board" / "sessions")
        self.state_dir.mkdir(parents=True, exist_ok=True)

    async def create_session(
        self,
        name: str | None = None,
        project_path: str | None = None,
        resume: str | bool | None = None,
        claude_args: list[str] | None = None,
    ) -> ChatSession:
        """
        Create and start a new chat session.

        Args:
            name: Optional friendly name
            project_path: Project directory (defaults to cwd)
            resume: Resume option for Claude Code
            claude_args: Additional claude arguments

        Returns:
            The created session
        """
        session = ChatSession(
            name=name,
            project_path=project_path or os.getcwd(),
        )

        await session.start(resume=resume, claude_args=claude_args)

        self.sessions[session.session_id] = session
        self._save_session_metadata(session)

        return session

    def get_session(self, session_id: str) -> ChatSession | None:
        """Get a session by ID or name"""
        # Try direct ID match
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Try name match
        for session in self.sessions.values():
            if session.name == session_id:
                return session

        return None

    def get_sessions_for_project(self, project_path: str) -> list[ChatSession]:
        """Get all sessions for a specific project"""
        normalized = os.path.abspath(project_path)
        return [
            s for s in self.sessions.values()
            if os.path.abspath(s.project_path) == normalized
        ]

    def get_active_sessions(self) -> list[ChatSession]:
        """Get all active (alive) sessions"""
        return [s for s in self.sessions.values() if s.is_alive()]

    def list_sessions(self) -> list[dict[str, object]]:
        """List all sessions as dictionaries"""
        return [s.to_dict() for s in self.sessions.values()]

    async def stop_session(self, session_id: str, force: bool = False) -> bool:
        """
        Stop a session.

        Returns True if session was found and stopped.
        """
        session = self.get_session(session_id)
        if not session:
            return False

        await session.stop(force=force)
        self._remove_session_metadata(session)
        del self.sessions[session.session_id]
        return True

    async def stop_all_sessions(self) -> None:
        """Stop all sessions"""
        for session in list(self.sessions.values()):
            await session.stop()
        self.sessions.clear()

    def _save_session_metadata(self, session: ChatSession) -> None:
        """Save session metadata to disk"""
        import json

        metadata_file = self.state_dir / f"{session.session_id}.json"
        metadata = {
            "session_id": session.session_id,
            "name": session.name,
            "project_path": session.project_path,
            "created_at": session.created_at.isoformat(),
            "pid": session.process.pid if session.process else None,
        }

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def _remove_session_metadata(self, session: ChatSession) -> None:
        """Remove session metadata from disk"""
        metadata_file = self.state_dir / f"{session.session_id}.json"
        metadata_file.unlink(missing_ok=True)

    def cleanup_dead_sessions(self) -> int:
        """
        Remove sessions that are no longer alive.

        Returns the number of sessions removed.
        """
        dead_sessions = [
            s for s in self.sessions.values()
            if not s.is_alive()
        ]

        for session in dead_sessions:
            self._remove_session_metadata(session)
            del self.sessions[session.session_id]

        return len(dead_sessions)
