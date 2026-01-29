"""
Claude Board CLI

Command-line interface for Claude Board:
- serve: Start the web server
- install: Install hooks into Claude Code settings
- uninstall: Remove hooks from Claude Code settings
- status: Show current status
- config: Show/edit configuration

Future commands:
- ble: Bluetooth device management
"""

import os
import signal
import socket
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import qrcode

from . import __app_name__, __version__
from .config import (
    CLAUDE_LOCAL_SETTINGS_FILE,
    CLAUDE_SETTINGS_FILE,
    AppConfig,
    ClaudeSettingsManager,
)

# Default paths
DEFAULT_SOCKET_PATH = Path.home() / ".claude-board" / "claude-board.sock"
DEFAULT_PID_FILE = Path.home() / ".claude-board" / "claude-board.pid"

# Initialize CLI app
app = typer.Typer(
    name=__app_name__,
    help="Physical console for Claude Code - approve/deny permissions from your phone or (future) hardware device.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold]{__app_name__}[/bold] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """
    Claude Board - Permission approval console for Claude Code

    Use your phone or a physical device to approve/deny Claude Code's
    permission requests.
    """
    pass


def get_primary_interface() -> Optional[str]:
    """
    Get the primary network interface using the default route.

    On macOS: uses 'route -n get default'
    On Linux: uses 'ip route show default'

    Returns:
        The interface name (e.g., 'en0', 'eth0') or None if not found.
    """
    import subprocess

    try:
        if sys.platform == "darwin":
            # macOS: use route -n get default
            result = subprocess.run(
                ["route", "-n", "get", "default"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith("interface:"):
                    return line.split(":", 1)[1].strip()
        else:
            # Linux: use ip route show default
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Output: "default via 192.168.1.1 dev eth0 proto ..."
            parts = result.stdout.strip().split()
            if "dev" in parts:
                dev_idx = parts.index("dev")
                if dev_idx + 1 < len(parts):
                    return parts[dev_idx + 1]
    except Exception:
        pass

    return None


def get_network_interfaces() -> List[Tuple[str, str, bool]]:
    """
    Get all network interfaces with their IP addresses.

    Returns:
        List of tuples: (interface_name, ip_address, is_primary)
        Sorted with primary interface first.
    """
    import subprocess

    interfaces = []

    # Get the primary interface from default route
    primary_iface = get_primary_interface()

    # Get all interfaces using system commands
    try:
        if sys.platform == "darwin":
            # macOS: use ifconfig
            result = subprocess.run(
                ["ifconfig"],
                capture_output=True,
                text=True,
                timeout=5
            )
            current_iface = None
            for line in result.stdout.split("\n"):
                if line and not line.startswith("\t") and not line.startswith(" "):
                    # Interface line: "en0: flags=..."
                    current_iface = line.split(":")[0]
                elif "inet " in line and current_iface:
                    # IP line: "	inet 192.168.1.100 netmask..."
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip = parts[1]
                        # Skip loopback
                        if not ip.startswith("127."):
                            is_primary = (current_iface == primary_iface)
                            interfaces.append((current_iface, ip, is_primary))
        else:
            # Linux: use ip addr
            result = subprocess.run(
                ["ip", "addr"],
                capture_output=True,
                text=True,
                timeout=5
            )
            current_iface = None
            for line in result.stdout.split("\n"):
                if ": " in line and not line.startswith(" "):
                    # Interface line: "2: eth0: <BROADCAST..."
                    parts = line.split(": ")
                    if len(parts) >= 2:
                        current_iface = parts[1].split("@")[0]
                elif "inet " in line and current_iface:
                    # IP line: "    inet 192.168.1.100/24..."
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip = parts[1].split("/")[0]
                        # Skip loopback
                        if not ip.startswith("127."):
                            is_primary = (current_iface == primary_iface)
                            interfaces.append((current_iface, ip, is_primary))
    except Exception:
        pass

    # Fallback: if no primary found but we have interfaces, try socket method
    if interfaces and not any(is_primary for _, _, is_primary in interfaces):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            s.close()
            # Mark the interface with this IP as primary
            interfaces = [
                (iface, ip, ip == primary_ip)
                for iface, ip, _ in interfaces
            ]
        except Exception:
            pass

    # Sort: primary first, then by interface name
    interfaces.sort(key=lambda x: (not x[2], x[0]))

    return interfaces


def get_local_ip() -> str:
    """Get the local IP address for mobile access (legacy function)"""
    interfaces = get_network_interfaces()
    for iface, ip, is_primary in interfaces:
        if is_primary:
            return ip
    if interfaces:
        return interfaces[0][1]
    return "unknown"


def _write_pid_file(pid: int) -> None:
    """Write PID to file for daemon management"""
    DEFAULT_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_PID_FILE.write_text(str(pid))


def _read_pid_file() -> Optional[int]:
    """Read PID from file, return None if not exists or invalid"""
    if not DEFAULT_PID_FILE.exists():
        return None
    try:
        pid = int(DEFAULT_PID_FILE.read_text().strip())
        # Check if process is running
        os.kill(pid, 0)
        return pid
    except (ValueError, ProcessLookupError, PermissionError):
        # Invalid PID or process not running
        DEFAULT_PID_FILE.unlink(missing_ok=True)
        return None


def _remove_pid_file() -> None:
    """Remove PID file"""
    DEFAULT_PID_FILE.unlink(missing_ok=True)


def _format_network_urls(port: int) -> str:
    """Format network URLs for display with primary interface first"""
    interfaces = get_network_interfaces()
    lines = [f"[dim]Local:[/dim]      http://localhost:{port}"]

    for i, (iface, ip, is_primary) in enumerate(interfaces):
        if is_primary:
            lines.append(f"[bold]Network:[/bold]    http://{ip}:{port}  [green]← primary ({iface})[/green]")
        else:
            lines.append(f"[dim]Network:[/dim]    http://{ip}:{port}  [dim]({iface})[/dim]")

    return "\n".join(lines)


def _print_qr_code(url: str) -> None:
    """Print QR code to terminal for easy mobile access"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Print QR code using Unicode block characters
    # Use inverted colors (white on black background) for better scanning
    # We use the half-block technique for better terminal rendering
    matrix = qr.get_matrix()
    rows = len(matrix)

    # Process two rows at a time using half-blocks
    # Inverted: QR dark modules become spaces, light modules become blocks
    output_lines = []
    for y in range(0, rows, 2):
        line = ""
        for x in range(len(matrix[0])):
            top = matrix[y][x] if y < rows else False
            bottom = matrix[y + 1][x] if y + 1 < rows else False

            # Inverted logic for white-on-black display
            if not top and not bottom:
                line += "█"  # Full block (both light in QR = black in terminal)
            elif not top:
                line += "▀"  # Upper half block
            elif not bottom:
                line += "▄"  # Lower half block
            else:
                line += " "  # Empty (both dark in QR = white/empty in terminal)
        output_lines.append(line)

    # Print with some padding
    console.print("\n[dim]Scan to open on mobile:[/dim]")
    console.print(f"  [dim]{url}[/dim]")
    console.print()
    for line in output_lines:
        console.print(f"  {line}")
    console.print()


@app.command()
def serve(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind to (0.0.0.0 for all interfaces).",
    ),
    port: int = typer.Option(
        8765,
        "--port",
        "-p",
        help="Port to listen on.",
    ),
    open_browser: bool = typer.Option(
        False,
        "--open",
        "-o",
        help="Open browser after starting server.",
    ),
    daemon: bool = typer.Option(
        False,
        "--daemon",
        "-d",
        help="Run server in background (daemon mode).",
    ),
    rpc_socket: Optional[str] = typer.Option(
        None,
        "--rpc-socket",
        help=f"Unix socket path for RPC API (default: {DEFAULT_SOCKET_PATH}).",
    ),
):
    """
    Start the Claude Board web server.

    The server receives permission requests from Claude Code hooks
    and serves a web UI for approving/denying them.

    Use --daemon to run in background. The server exposes a Unix socket
    RPC API for programmatic control (useful for GUI tools).
    """
    from .server import run_server

    # Check if already running
    existing_pid = _read_pid_file()
    if existing_pid:
        console.print(f"[yellow]Server already running (PID: {existing_pid})[/yellow]")
        console.print(f"Use [bold]claude-board stop[/bold] to stop it first.")
        raise typer.Exit(1)

    # Determine socket path
    socket_path = Path(rpc_socket) if rpc_socket else DEFAULT_SOCKET_PATH

    network_urls = _format_network_urls(port)

    if daemon:
        # Fork to background using double fork technique
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process - wait for grandchild to write PID file
                import time
                for _ in range(20):  # Wait up to 2 seconds
                    time.sleep(0.1)
                    daemon_pid = _read_pid_file()
                    if daemon_pid:
                        # Also check if server is actually responding
                        try:
                            import urllib.request
                            with urllib.request.urlopen(f"http://localhost:{port}/api/health", timeout=1):
                                break
                        except Exception:
                            continue

                daemon_pid = _read_pid_file()
                if daemon_pid:
                    console.print(Panel.fit(
                        f"[bold green]Claude Board Server (daemon)[/bold green]\n\n"
                        f"{network_urls}\n\n"
                        f"[dim]RPC Socket:[/dim]  {socket_path}\n"
                        f"[dim]PID:[/dim]         {daemon_pid}\n\n"
                        f"[yellow]Open the URL on your phone to approve/deny requests[/yellow]\n\n"
                        f"Stop with: [bold]claude-board stop[/bold]",
                        title="Server Started",
                        border_style="green",
                    ))

                    # Print QR code for primary network interface
                    interfaces = get_network_interfaces()
                    for iface, ip, is_primary in interfaces:
                        if is_primary:
                            _print_qr_code(f"http://{ip}:{port}")
                            break

                    if open_browser:
                        import webbrowser
                        webbrowser.open(f"http://localhost:{port}")

                    raise typer.Exit(0)
                else:
                    console.print("[red]Failed to start daemon[/red]")
                    console.print(f"[dim]Check log: {DEFAULT_PID_FILE.parent / 'server.log'}[/dim]")
                    raise typer.Exit(1)
        except OSError as e:
            console.print(f"[red]Fork failed: {e}[/red]")
            raise typer.Exit(1)

        # First child process - detach from terminal
        os.setsid()

        # Second fork to prevent zombie processes
        try:
            pid = os.fork()
            if pid > 0:
                # First child exits, grandchild continues
                sys.exit(0)
        except OSError:
            sys.exit(1)

        # Grandchild process - this is the actual daemon
        # Write PID file first
        _write_pid_file(os.getpid())

        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()

        # Close stdin, redirect stdout/stderr to log file
        log_file = DEFAULT_PID_FILE.parent / "server.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open("/dev/null", "r") as devnull:
            os.dup2(devnull.fileno(), sys.stdin.fileno())
        with open(log_file, "a") as log:
            os.dup2(log.fileno(), sys.stdout.fileno())
            os.dup2(log.fileno(), sys.stderr.fileno())

        # Run server
        try:
            config = AppConfig()
            config.server.host = host
            config.server.port = port
            run_server(host=host, port=port, config=config, socket_path=socket_path)
        finally:
            _remove_pid_file()
            # Clean up socket file
            if socket_path.exists():
                socket_path.unlink()
    else:
        # Foreground mode
        console.print(Panel.fit(
            f"[bold green]Claude Board Server[/bold green]\n\n"
            f"{network_urls}\n\n"
            f"[dim]RPC Socket:[/dim]  {socket_path}\n\n"
            f"[yellow]Open the URL on your phone to approve/deny requests[/yellow]\n\n"
            f"Press [bold]Ctrl+C[/bold] to stop",
            title="Starting Server",
            border_style="green",
        ))

        # Print QR code for primary network interface
        interfaces = get_network_interfaces()
        for iface, ip, is_primary in interfaces:
            if is_primary:
                _print_qr_code(f"http://{ip}:{port}")
                break

        if open_browser:
            import webbrowser
            webbrowser.open(f"http://localhost:{port}")

        # Write PID file even in foreground mode
        _write_pid_file(os.getpid())

        try:
            config = AppConfig()
            config.server.host = host
            config.server.port = port
            run_server(host=host, port=port, config=config, socket_path=socket_path)
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped.[/yellow]")
        finally:
            _remove_pid_file()
            # Clean up socket file
            if socket_path.exists():
                socket_path.unlink()


@app.command()
def stop():
    """
    Stop the running Claude Board server (daemon mode).
    """
    pid = _read_pid_file()
    if not pid:
        console.print("[yellow]No server is running.[/yellow]")
        raise typer.Exit(0)

    try:
        os.kill(pid, signal.SIGTERM)
        console.print(f"[green]Server stopped (PID: {pid})[/green]")
        _remove_pid_file()
        # Clean up socket file
        if DEFAULT_SOCKET_PATH.exists():
            DEFAULT_SOCKET_PATH.unlink()
    except ProcessLookupError:
        console.print("[yellow]Server process not found, cleaning up...[/yellow]")
        _remove_pid_file()
    except PermissionError:
        console.print(f"[red]Permission denied to stop server (PID: {pid})[/red]")
        raise typer.Exit(1)


@app.command()
def install(
    scope: str = typer.Option(
        "user",
        "--scope",
        "-s",
        help="Where to install hooks: 'user' (~/.claude/settings.json) or 'local' (project .claude/settings.local.json).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Reinstall even if already installed.",
    ),
):
    """
    Install Claude Board hooks into Claude Code settings.

    This adds hooks that redirect permission requests to the Claude Board
    server. Your existing hooks are preserved.

    After installing, restart Claude Code to load the new hooks.
    """
    # Determine settings file
    if scope == "user":
        settings_file = CLAUDE_SETTINGS_FILE
    elif scope == "local":
        settings_file = CLAUDE_LOCAL_SETTINGS_FILE
    else:
        console.print(f"[red]Invalid scope: {scope}. Use 'user' or 'local'.[/red]")
        raise typer.Exit(1)

    manager = ClaudeSettingsManager(settings_file)

    # Check if already installed
    if manager.is_installed() and not force:
        console.print("[yellow]Claude Board hooks are already installed.[/yellow]")
        console.print("Use [bold]--force[/bold] to reinstall.")
        raise typer.Exit(0)

    # Install hooks
    try:
        manager.install_hooks()
        console.print(Panel.fit(
            f"[bold green]Hooks installed successfully![/bold green]\n\n"
            f"[dim]Settings file:[/dim] {settings_file}\n\n"
            f"[yellow]Important:[/yellow] Restart Claude Code to load the hooks.\n\n"
            f"Then start the server with:\n"
            f"  [bold]claude-board serve[/bold]",
            title="Installation Complete",
            border_style="green",
        ))
    except Exception as e:
        console.print(f"[red]Failed to install hooks: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def uninstall(
    scope: str = typer.Option(
        "user",
        "--scope",
        "-s",
        help="Where to uninstall from: 'user' or 'local'.",
    ),
    all_scopes: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Uninstall from all scopes (user and local).",
    ),
):
    """
    Remove Claude Board hooks from Claude Code settings.

    Your other hooks are preserved.
    """
    scopes_to_uninstall = []

    if all_scopes:
        scopes_to_uninstall = [
            ("user", CLAUDE_SETTINGS_FILE),
            ("local", CLAUDE_LOCAL_SETTINGS_FILE),
        ]
    elif scope == "user":
        scopes_to_uninstall = [("user", CLAUDE_SETTINGS_FILE)]
    elif scope == "local":
        scopes_to_uninstall = [("local", CLAUDE_LOCAL_SETTINGS_FILE)]
    else:
        console.print(f"[red]Invalid scope: {scope}[/red]")
        raise typer.Exit(1)

    uninstalled = []
    for scope_name, settings_file in scopes_to_uninstall:
        manager = ClaudeSettingsManager(settings_file)
        if manager.is_installed():
            try:
                manager.uninstall_hooks()
                uninstalled.append(scope_name)
            except Exception as e:
                console.print(f"[red]Failed to uninstall from {scope_name}: {e}[/red]")

    if uninstalled:
        console.print(f"[green]Hooks uninstalled from: {', '.join(uninstalled)}[/green]")
        console.print("[yellow]Restart Claude Code to apply changes.[/yellow]")
    else:
        console.print("[yellow]No hooks were installed.[/yellow]")


@app.command()
def status():
    """
    Show the current status of Claude Board.

    Displays:
    - Hook installation status
    - Server availability
    - Configuration
    """
    # Check hooks status
    table = Table(title="Claude Board Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    # User hooks
    user_manager = ClaudeSettingsManager(CLAUDE_SETTINGS_FILE)
    user_status = user_manager.get_hooks_status()
    table.add_row(
        "User hooks (~/.claude/settings.json)",
        "[green]Installed[/green]" if user_status.installed else "[dim]Not installed[/dim]"
    )

    # Local hooks
    local_manager = ClaudeSettingsManager(CLAUDE_LOCAL_SETTINGS_FILE)
    local_status = local_manager.get_hooks_status()
    table.add_row(
        "Local hooks (.claude/settings.local.json)",
        "[green]Installed[/green]" if local_status.installed else "[dim]Not installed[/dim]"
    )

    # Server status
    config = AppConfig()
    server_url = f"http://localhost:{config.server.port}"
    server_running = False
    try:
        import urllib.request
        with urllib.request.urlopen(f"{server_url}/api/health", timeout=2) as resp:
            data = resp.read()
            table.add_row("Server", f"[green]Running[/green] at {server_url}")
            server_running = True
    except Exception:
        table.add_row("Server", f"[dim]Not running[/dim] (start with [bold]claude-board serve[/bold])")

    # Network info - show all interfaces
    interfaces = get_network_interfaces()
    if interfaces:
        for i, (iface, ip, is_primary) in enumerate(interfaces):
            label = "Primary Network" if is_primary else f"Network ({iface})"
            url = f"http://{ip}:{config.server.port}"
            if is_primary:
                table.add_row(label, f"[bold]{url}[/bold]")
            else:
                table.add_row(label, f"[dim]{url}[/dim]")
    else:
        table.add_row("Network", "[dim]Unknown[/dim]")

    # RPC Socket status
    if DEFAULT_SOCKET_PATH.exists():
        table.add_row("RPC Socket", f"[green]{DEFAULT_SOCKET_PATH}[/green]")
    else:
        table.add_row("RPC Socket", f"[dim]Not active[/dim]")

    console.print(table)

    # Show detailed hook info if installed
    if user_status.installed or local_status.installed:
        console.print("\n[dim]Installed hooks:[/dim]")
        for hook in user_status.our_hooks + local_status.our_hooks:
            console.print(f"  • {hook.event}: {hook.matcher}")

        if user_status.other_hooks_count + local_status.other_hooks_count > 0:
            total_other = user_status.other_hooks_count + local_status.other_hooks_count
            console.print(f"\n[dim]Other hooks preserved: {total_other}[/dim]")

    # Show QR code if server is running
    if server_running and interfaces:
        for iface, ip, is_primary in interfaces:
            if is_primary:
                _print_qr_code(f"http://{ip}:{config.server.port}")
                break


@app.command()
def config(
    show: bool = typer.Option(
        True,
        "--show/--no-show",
        help="Show current configuration.",
    ),
    port: Optional[int] = typer.Option(
        None,
        "--port",
        "-p",
        help="Set default server port.",
    ),
    yolo: Optional[bool] = typer.Option(
        None,
        "--yolo/--no-yolo",
        help="Set default YOLO mode.",
    ),
):
    """
    Show or modify Claude Board configuration.
    """
    app_config = AppConfig()

    # Apply changes
    changed = False
    if port is not None:
        app_config.server.port = port
        changed = True
    if yolo is not None:
        app_config.yolo_mode_default = yolo
        changed = True

    if changed:
        # Save to user config directory
        config_path = Path.home() / ".claude-board" / "config.json"
        app_config.save(config_path)
        console.print(f"[green]Configuration saved to {config_path}[/green]")

    if show:
        table = Table(title="Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Server Host", app_config.server.host)
        table.add_row("Server Port", str(app_config.server.port))
        table.add_row("Hook Timeout", f"{app_config.server.hook_timeout}s")
        table.add_row("YOLO Default", str(app_config.yolo_mode_default))
        table.add_row("Safe Tools", ", ".join(app_config.hooks.safe_tools[:5]) + "...")
        table.add_row("Bluetooth", "[dim]Not yet implemented[/dim]")

        console.print(table)


@app.command()
def qr(
    port: Optional[int] = typer.Option(
        None,
        "--port",
        "-p",
        help="Port number (default: from config or 8765).",
    ),
):
    """
    Display QR code for mobile access.

    Shows a scannable QR code for the primary network interface URL.
    Useful for quickly connecting from a mobile device.
    """
    app_config = AppConfig()
    actual_port = port or app_config.server.port

    interfaces = get_network_interfaces()
    if not interfaces:
        console.print("[red]No network interfaces found.[/red]")
        raise typer.Exit(1)

    # Find primary interface
    primary_url = None
    for iface, ip, is_primary in interfaces:
        if is_primary:
            primary_url = f"http://{ip}:{actual_port}"
            console.print(f"[bold]Primary interface:[/bold] {iface} ({ip})")
            break

    if not primary_url:
        # Fallback to first interface
        iface, ip, _ = interfaces[0]
        primary_url = f"http://{ip}:{actual_port}"
        console.print(f"[bold]Interface:[/bold] {iface} ({ip})")

    _print_qr_code(primary_url)

    # Show all interfaces
    if len(interfaces) > 1:
        console.print("[dim]Other interfaces:[/dim]")
        for iface, ip, is_primary in interfaces:
            if not is_primary:
                console.print(f"  [dim]{iface}: http://{ip}:{actual_port}[/dim]")


# Future: Bluetooth commands
@app.command(hidden=True)
def ble():
    """
    [Future] Bluetooth device management.

    This command will be available in Phase 2 when Bluetooth
    support is implemented.
    """
    console.print(Panel.fit(
        "[yellow]Bluetooth support is planned for Phase 2.[/yellow]\n\n"
        "The physical console will feature:\n"
        "• 4 mechanical key switches (Approve, Deny, Retry, YOLO)\n"
        "• E-ink display for task status\n"
        "• Bluetooth LE connection\n"
        "• Battery powered\n\n"
        "[dim]Stay tuned![/dim]",
        title="Coming Soon",
        border_style="yellow",
    ))


@app.command()
def rpc(
    method: str = typer.Argument(
        ...,
        help="RPC method to call (get_state, approve, deny, set_yolo, reset, health)",
    ),
    params: Optional[str] = typer.Argument(
        None,
        help="JSON params for the method (e.g., '{\"request_id\": \"abc\"}')",
    ),
    socket_path: Optional[str] = typer.Option(
        None,
        "--socket",
        "-s",
        help=f"Unix socket path (default: {DEFAULT_SOCKET_PATH})",
    ),
):
    """
    Call the Claude Board RPC API.

    This allows programmatic control of the server from scripts or GUI tools.

    Examples:
        claude-board rpc health
        claude-board rpc get_state
        claude-board rpc approve '{"request_id": "abc123"}'
        claude-board rpc set_yolo '{"enabled": true}'
    """
    import json as json_module

    sock_path = Path(socket_path) if socket_path else DEFAULT_SOCKET_PATH

    if not sock_path.exists():
        console.print(f"[red]RPC socket not found: {sock_path}[/red]")
        console.print("Is the server running? Start with: [bold]claude-board serve[/bold]")
        raise typer.Exit(1)

    # Parse params
    parsed_params = {}
    if params:
        try:
            parsed_params = json_module.loads(params)
        except json_module.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON params: {e}[/red]")
            raise typer.Exit(1)

    # Build JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": parsed_params,
        "id": 1
    }

    try:
        # Connect to Unix socket
        import socket as sock_module
        client = sock_module.socket(sock_module.AF_UNIX, sock_module.SOCK_STREAM)
        client.connect(str(sock_path))
        client.settimeout(5.0)

        # Send request
        client.sendall((json_module.dumps(request) + "\n").encode("utf-8"))

        # Read response
        response_data = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response_data += chunk
            if b"\n" in response_data:
                break

        client.close()

        # Parse response
        response = json_module.loads(response_data.decode("utf-8"))

        if "error" in response:
            console.print(f"[red]Error:[/red] {response['error']['message']}")
            raise typer.Exit(1)

        # Pretty print result
        result = response.get("result", {})
        console.print_json(json_module.dumps(result, indent=2, default=str))

    except FileNotFoundError:
        console.print(f"[red]Socket not found: {sock_path}[/red]")
        raise typer.Exit(1)
    except ConnectionRefusedError:
        console.print(f"[red]Connection refused. Is the server running?[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]RPC error: {e}[/red]")
        raise typer.Exit(1)


@app.command(hidden=True)
def hook(
    hook_type: str = typer.Argument(
        "permission",
        help="Hook type: 'permission' or 'todo'",
    ),
):
    """
    Internal command called by Claude Code hooks.

    This is not meant to be called directly by users.
    It reads JSON from stdin and outputs JSON to stdout.
    """
    import json
    import sys

    if hook_type == "permission":
        from .hooks.permission_hook import main as permission_main
        permission_main()
    elif hook_type == "todo":
        from .hooks.todo_hook import main as todo_main
        todo_main()
    else:
        print(f"Unknown hook type: {hook_type}", file=sys.stderr)
        sys.exit(1)


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
