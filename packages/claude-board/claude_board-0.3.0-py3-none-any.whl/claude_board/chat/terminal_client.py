"""
Terminal Client for Claude Board Chat Sessions

Allows users to attach to a running chat session from their terminal.
Provides:
- Raw terminal mode for proper Claude Code TUI rendering
- Keyboard input forwarding
- Detach support (Ctrl+Q)
- Terminal resize handling

Clients:
- TerminalClient: Connects via Unix socket (for local daemon)
- DirectTerminalClient: Uses PTY directly (same process)
- WebSocketTerminalClient: Connects via WebSocket to server API
"""

from __future__ import annotations

import asyncio
import json
import os
import select
import signal
import sys
import termios
import tty
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class TerminalClient:
    """
    Terminal client that attaches to a chat session.

    Uses raw terminal mode to properly display Claude Code's TUI
    and forward all keyboard input.
    """

    DETACH_KEY = b"\x11"  # Ctrl+Q

    def __init__(
        self,
        session_socket: Path | str,
        detach_key: bytes = DETACH_KEY,
    ) -> None:
        """
        Initialize terminal client.

        Args:
            session_socket: Path to the session's Unix socket
            detach_key: Key sequence to detach (default: Ctrl+Q)
        """
        self.socket_path = Path(session_socket)
        self.detach_key = detach_key
        self.original_termios: Any = None
        self.original_sigwinch: Any = None
        self._running = False
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def attach(self) -> int:
        """
        Attach to the session.

        Returns exit code:
        - 0: Clean detach
        - 1: Error
        - 2: Session ended
        """
        if not self.socket_path.exists():
            print(f"Session socket not found: {self.socket_path}", file=sys.stderr)
            return 1

        # Save terminal state
        if sys.stdin.isatty():
            self.original_termios = termios.tcgetattr(sys.stdin.fileno())

        try:
            # Set terminal to raw mode
            if self.original_termios:
                tty.setraw(sys.stdin.fileno())

            # Connect to session daemon
            self._reader, self._writer = await asyncio.open_unix_connection(
                str(self.socket_path)
            )

            # Send ATTACH command
            await self._send_command("ATTACH")

            # Send initial terminal size
            await self._send_resize()

            # Set up SIGWINCH handler for terminal resize
            loop = asyncio.get_event_loop()
            self.original_sigwinch = signal.getsignal(signal.SIGWINCH)
            signal.signal(
                signal.SIGWINCH,
                lambda *_: loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self._send_resize())
                )
            )

            # Run I/O loops
            self._running = True
            result = await self._run_io_loops()

            return result

        except ConnectionRefusedError:
            print("Connection refused. Is the session running?", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        finally:
            await self._cleanup()

    async def _run_io_loops(self) -> int:
        """Run the main I/O loops"""
        stdin_task = asyncio.create_task(self._forward_stdin())
        output_task = asyncio.create_task(self._forward_output())

        try:
            done, pending = await asyncio.wait(
                [stdin_task, output_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Get result from completed task
            for task in done:
                try:
                    return task.result()
                except Exception:
                    return 1

            return 0

        except asyncio.CancelledError:
            return 0

    async def _forward_stdin(self) -> int:
        """Forward stdin to session"""
        loop = asyncio.get_event_loop()

        while self._running:
            try:
                # Wait for stdin to be readable
                readable, _, _ = await loop.run_in_executor(
                    None,
                    lambda: select.select([sys.stdin], [], [], 0.1)
                )

                if not readable:
                    continue

                # Read from stdin
                data = await loop.run_in_executor(
                    None,
                    lambda: os.read(sys.stdin.fileno(), 1024)
                )

                if not data:
                    return 2  # EOF

                # Check for detach key
                if self.detach_key in data:
                    await self._send_command("DETACH")
                    return 0  # Clean detach

                # Send input to session
                await self._send_input(data)

            except OSError:
                return 1

        return 0

    async def _forward_output(self) -> int:
        """Forward session output to stdout"""
        if not self._reader:
            return 1

        while self._running:
            try:
                # Read from session
                data = await self._reader.read(4096)

                if not data:
                    return 2  # Session ended

                # Check for protocol messages
                if data.startswith(b"MSG:"):
                    msg = data[4:].decode("utf-8", errors="replace").strip()
                    if msg == "DETACHED":
                        return 0
                    elif msg == "SESSION_ENDED":
                        return 2
                    continue

                # Write to stdout
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

            except asyncio.CancelledError:
                break
            except Exception:
                return 1

        return 0

    async def _send_command(self, command: str) -> None:
        """Send a protocol command"""
        if self._writer:
            self._writer.write(f"CMD:{command}\n".encode("utf-8"))
            await self._writer.drain()

    async def _send_input(self, data: bytes) -> None:
        """Send input data"""
        if self._writer:
            # Use length-prefixed binary for input
            length = len(data)
            self._writer.write(f"INPUT:{length}:".encode("utf-8") + data)
            await self._writer.drain()

    async def _send_resize(self) -> None:
        """Send terminal size"""
        if not self._writer:
            return

        try:
            if sys.stdout.isatty():
                size = os.get_terminal_size()
                await self._send_command(f"RESIZE:{size.lines}:{size.columns}")
        except (OSError, ValueError):
            pass

    async def _cleanup(self) -> None:
        """Clean up resources"""
        self._running = False

        # Restore terminal
        if self.original_termios and sys.stdin.isatty():
            try:
                termios.tcsetattr(
                    sys.stdin.fileno(),
                    termios.TCSADRAIN,
                    self.original_termios
                )
            except Exception:
                pass

        # Restore signal handler
        if self.original_sigwinch is not None:
            signal.signal(signal.SIGWINCH, self.original_sigwinch)

        # Close connection
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass

        # Print newline to avoid prompt on same line
        print()


class DirectTerminalClient:
    """
    Direct terminal client that uses PTY directly (without socket).

    Used when running in the same process as the session manager.
    """

    DETACH_KEY = b"\x11"  # Ctrl+Q

    def __init__(self, detach_key: bytes = DETACH_KEY) -> None:
        self.detach_key = detach_key
        self.original_termios: Any = None
        self.original_sigwinch: Any = None
        self._running = False
        self._session = None

    async def attach(self, session) -> int:
        """
        Attach directly to a ChatSession.

        Args:
            session: The ChatSession to attach to

        Returns:
            Exit code (0=detach, 1=error, 2=session ended)
        """
        from .session import ChatSession

        if not isinstance(session, ChatSession):
            print("Invalid session", file=sys.stderr)
            return 1

        self._session = session

        # Save terminal state
        if sys.stdin.isatty():
            self.original_termios = termios.tcgetattr(sys.stdin.fileno())

        try:
            # Set terminal to raw mode
            if self.original_termios:
                tty.setraw(sys.stdin.fileno())

            # Send terminal size to session
            self._send_resize()

            # Set up SIGWINCH handler
            loop = asyncio.get_event_loop()
            self.original_sigwinch = signal.getsignal(signal.SIGWINCH)
            signal.signal(
                signal.SIGWINCH,
                lambda *_: loop.call_soon_threadsafe(self._send_resize)
            )

            # Attach for output
            stdout_fd = sys.stdout.fileno()
            history = session.attach_terminal(stdout_fd)

            # Replay history
            if history:
                sys.stdout.buffer.write(history)
                sys.stdout.buffer.flush()

            # Run I/O loop
            self._running = True
            result = await self._run_stdin_loop()

            return result

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        finally:
            await self._cleanup()

    async def _run_stdin_loop(self) -> int:
        """Forward stdin to session"""
        loop = asyncio.get_event_loop()

        while self._running and self._session and self._session.is_alive():
            try:
                # Wait for stdin
                readable, _, _ = await loop.run_in_executor(
                    None,
                    lambda: select.select([sys.stdin], [], [], 0.1)
                )

                if not readable:
                    # Check if session is still alive
                    if not self._session.is_alive():
                        return 2
                    continue

                # Read from stdin
                data = await loop.run_in_executor(
                    None,
                    lambda: os.read(sys.stdin.fileno(), 1024)
                )

                if not data:
                    return 2  # EOF

                # Check for detach key
                if self.detach_key in data:
                    return 0  # Clean detach

                # Send to session
                await self._session.send_input(data, source="terminal")

            except OSError:
                return 1

        return 2 if not self._session or not self._session.is_alive() else 0

    def _send_resize(self) -> None:
        """Send terminal size to session"""
        if not self._session:
            return

        try:
            if sys.stdout.isatty():
                size = os.get_terminal_size()
                self._session.resize(size.lines, size.columns)
        except (OSError, ValueError):
            pass

    async def _cleanup(self) -> None:
        """Clean up resources"""
        self._running = False

        # Detach from session
        if self._session:
            self._session.detach_terminal(sys.stdout.fileno())

        # Restore terminal
        if self.original_termios and sys.stdin.isatty():
            try:
                termios.tcsetattr(
                    sys.stdin.fileno(),
                    termios.TCSADRAIN,
                    self.original_termios
                )
            except Exception:
                pass

        # Restore signal handler
        if self.original_sigwinch is not None:
            signal.signal(signal.SIGWINCH, self.original_sigwinch)

        # Print newline
        print()


class WebSocketTerminalClient:
    """
    Terminal client that connects to a session via WebSocket.

    Used when sessions are managed by a remote server process.
    Connects to the server's /ws/sessions/{id}/terminal endpoint.
    """

    DETACH_KEY = b"\x11"  # Ctrl+Q

    def __init__(
        self,
        server_url: str,
        session_id: str,
        detach_key: bytes = DETACH_KEY,
    ) -> None:
        """
        Initialize WebSocket terminal client.

        Args:
            server_url: Base URL of the server (e.g., "http://127.0.0.1:8765")
            session_id: ID of the session to connect to
            detach_key: Key sequence to detach (default: Ctrl+Q)
        """
        self.server_url = server_url
        self.session_id = session_id
        self.detach_key = detach_key
        self.original_termios: Any = None
        self.original_sigwinch: Any = None
        self._running = False
        self._ws: Any = None

    async def attach(self) -> int:
        """
        Attach to the session via WebSocket.

        Returns exit code:
        - 0: Clean detach
        - 1: Error
        - 2: Session ended
        """
        try:
            import websockets
        except ImportError:
            print("websockets package required. Install with: pip install websockets", file=sys.stderr)
            return 1

        # Build WebSocket URL
        ws_url = self.server_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws/sessions/{self.session_id}/terminal"

        # Save terminal state
        if sys.stdin.isatty():
            self.original_termios = termios.tcgetattr(sys.stdin.fileno())

        try:
            # Set terminal to raw mode
            if self.original_termios:
                tty.setraw(sys.stdin.fileno())

            # Connect to WebSocket
            async with websockets.connect(ws_url) as ws:
                self._ws = ws

                # Send initial terminal size
                await self._send_resize()

                # Set up SIGWINCH handler
                loop = asyncio.get_event_loop()
                self.original_sigwinch = signal.getsignal(signal.SIGWINCH)
                signal.signal(
                    signal.SIGWINCH,
                    lambda *_: loop.call_soon_threadsafe(
                        lambda: asyncio.create_task(self._send_resize())
                    )
                )

                # Run I/O loops
                self._running = True
                result = await self._run_io_loops()

                return result

        except Exception as e:
            print(f"WebSocket error: {e}", file=sys.stderr)
            return 1
        finally:
            await self._cleanup()

    async def _run_io_loops(self) -> int:
        """Run the main I/O loops"""
        stdin_task = asyncio.create_task(self._forward_stdin())
        output_task = asyncio.create_task(self._forward_output())

        try:
            done, pending = await asyncio.wait(
                [stdin_task, output_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Get result from completed task
            for task in done:
                try:
                    return task.result()
                except Exception:
                    return 1

            return 0

        except asyncio.CancelledError:
            return 0

    async def _forward_stdin(self) -> int:
        """Forward stdin to WebSocket"""
        loop = asyncio.get_event_loop()

        while self._running and self._ws:
            try:
                # Wait for stdin to be readable
                readable, _, _ = await loop.run_in_executor(
                    None,
                    lambda: select.select([sys.stdin], [], [], 0.1)
                )

                if not readable:
                    continue

                # Read from stdin
                data = await loop.run_in_executor(
                    None,
                    lambda: os.read(sys.stdin.fileno(), 1024)
                )

                if not data:
                    return 2  # EOF

                # Check for detach key
                if self.detach_key in data:
                    return 0  # Clean detach

                # Send input via WebSocket (UTF-8 encoded)
                await self._ws.send(json.dumps({
                    "type": "input",
                    "data": data.decode("utf-8", errors="replace"),
                }))

            except OSError:
                return 1

        return 0

    async def _forward_output(self) -> int:
        """Forward WebSocket output to stdout"""
        if not self._ws:
            return 1

        while self._running:
            try:
                # Receive from WebSocket
                message = await self._ws.recv()

                # Parse JSON message
                try:
                    msg = json.loads(message)
                    msg_type = msg.get("type", "")

                    if msg_type == "output":
                        # Output is UTF-8 encoded string
                        data = msg.get("data", "")
                        sys.stdout.buffer.write(data.encode("utf-8"))
                        sys.stdout.buffer.flush()
                    elif msg_type == "history":
                        # Initial history replay
                        data = msg.get("data", "")
                        sys.stdout.buffer.write(data.encode("utf-8"))
                        sys.stdout.buffer.flush()
                    elif msg_type == "session_ended":
                        return 2
                    elif msg_type == "error":
                        print(f"\nError: {msg.get('message', 'Unknown error')}", file=sys.stderr)
                        return 1
                except json.JSONDecodeError:
                    # Raw data (fallback)
                    sys.stdout.buffer.write(message.encode() if isinstance(message, str) else message)
                    sys.stdout.buffer.flush()

            except asyncio.CancelledError:
                break
            except Exception:
                return 1

        return 0

    async def _send_resize(self) -> None:
        """Send terminal size via WebSocket"""
        if not self._ws:
            return

        try:
            if sys.stdout.isatty():
                size = os.get_terminal_size()
                await self._ws.send(json.dumps({
                    "type": "resize",
                    "rows": size.lines,
                    "cols": size.columns,
                }))
        except (OSError, ValueError):
            pass

    async def _cleanup(self) -> None:
        """Clean up resources"""
        self._running = False

        # Restore terminal
        if self.original_termios and sys.stdin.isatty():
            try:
                termios.tcsetattr(
                    sys.stdin.fileno(),
                    termios.TCSADRAIN,
                    self.original_termios
                )
            except Exception:
                pass

        # Restore signal handler
        if self.original_sigwinch is not None:
            signal.signal(signal.SIGWINCH, self.original_sigwinch)

        # Print newline
        print()
