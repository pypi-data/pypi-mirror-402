"""
Configuration management for Claude Board

Handles:
- Application configuration (server port, timeouts, etc.)
- Claude Code hooks configuration (install/uninstall)
- Future: Bluetooth device configuration
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from .types import HooksStatus, InstalledHookInfo

# Type alias for JSON-like dictionaries (used for settings manipulation)
# We use Any here because JSON settings have dynamic structure
JsonDict = dict[str, Any]

# Default paths
CLAUDE_DIR = Path.home() / ".claude"
CLAUDE_SETTINGS_FILE = CLAUDE_DIR / "settings.json"
CLAUDE_LOCAL_SETTINGS_FILE = CLAUDE_DIR / "settings.local.json"

# Marker to identify our hooks in user's config
HOOK_MARKER = "_claude_board"


@dataclass
class ServerConfig:
    """Web server configuration"""
    host: str = "0.0.0.0"
    port: int = 8765
    hook_timeout: int = 55  # Slightly less than Claude Code's 60s default


@dataclass
class HooksConfig:
    """Hooks behavior configuration"""
    # Tools that are always safe (auto-approve without sending to console)
    safe_tools: list[str] = field(default_factory=lambda: [
        "Glob", "Grep", "TodoWrite", "TodoRead", "Task", "WebSearch", "WebFetch"
    ])
    # Tools that require approval
    dangerous_tools: list[str] = field(default_factory=lambda: [
        "Write", "Edit", "Bash"
    ])
    # Auto-approve reads within these directories (relative to project)
    safe_read_patterns: list[str] = field(default_factory=lambda: [
        "."  # Current project directory
    ])


@dataclass
class BluetoothConfig:
    """Bluetooth configuration for future physical console"""
    enabled: bool = False
    device_name: str = "Claude Board"
    auto_connect: bool = True
    # Service UUIDs (will be defined in Phase 2)
    service_uuid: str = "12345678-1234-5678-1234-56789abcdef0"


@dataclass
class AppConfig:
    """Main application configuration"""

    server: ServerConfig = field(default_factory=ServerConfig)
    hooks: HooksConfig = field(default_factory=HooksConfig)
    bluetooth: BluetoothConfig = field(default_factory=BluetoothConfig)

    # YOLO mode default
    yolo_mode_default: bool = False

    @classmethod
    def load(cls, config_path: Path | None = None) -> AppConfig:
        """Load configuration from file or use defaults"""
        if config_path and config_path.exists():
            with open(config_path) as f:
                data: dict[str, object] = json.load(f)
            return cls.from_dict(data)
        return cls()

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AppConfig:
        """Create config from dictionary"""
        config = cls()
        if "server" in data and isinstance(data["server"], dict):
            config.server = ServerConfig(**data["server"])  # type: ignore[arg-type]
        if "hooks" in data and isinstance(data["hooks"], dict):
            config.hooks = HooksConfig(**data["hooks"])  # type: ignore[arg-type]
        if "bluetooth" in data and isinstance(data["bluetooth"], dict):
            config.bluetooth = BluetoothConfig(**data["bluetooth"])  # type: ignore[arg-type]
        if "yolo_mode_default" in data:
            config.yolo_mode_default = bool(data["yolo_mode_default"])
        return config

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary"""
        return {
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "hook_timeout": self.server.hook_timeout,
            },
            "hooks": {
                "safe_tools": self.hooks.safe_tools,
                "dangerous_tools": self.hooks.dangerous_tools,
                "safe_read_patterns": self.hooks.safe_read_patterns,
            },
            "bluetooth": {
                "enabled": self.bluetooth.enabled,
                "device_name": self.bluetooth.device_name,
                "auto_connect": self.bluetooth.auto_connect,
                "service_uuid": self.bluetooth.service_uuid,
            },
            "yolo_mode_default": self.yolo_mode_default,
        }

    def save(self, config_path: Path) -> None:
        """Save configuration to file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class ClaudeSettingsManager:
    """
    Manages Claude Code settings.json hooks configuration.

    Carefully preserves user's existing hooks while adding/removing our hooks.
    """

    def __init__(self, settings_file: Path = CLAUDE_SETTINGS_FILE) -> None:
        self.settings_file = settings_file

    def _load_settings(self) -> JsonDict:
        """Load existing settings or return empty dict"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file) as f:
                    result: JsonDict = json.load(f)
                    return result
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_settings(self, settings: JsonDict) -> None:
        """Save settings to file"""
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_file, "w") as f:
            json.dump(settings, f, indent=2)

    def _get_hook_script_path(self) -> str:
        """Get the path to our hook script (fallback for non-pip installs)"""
        # When installed via pip, the script will be in the package
        import claude_board.hooks.permission_hook as hook_module

        if hook_module.__file__ is None:
            raise RuntimeError("Cannot determine permission_hook module path")
        return str(Path(hook_module.__file__).resolve())

    def _get_todo_hook_script_path(self) -> str:
        """Get the path to our todo sync hook script (fallback for non-pip installs)"""
        import claude_board.hooks.todo_hook as hook_module

        if hook_module.__file__ is None:
            raise RuntimeError("Cannot determine todo_hook module path")
        return str(Path(hook_module.__file__).resolve())

    def _get_hook_command(self, hook_type: str) -> str:
        """
        Get the command to run a hook.

        Tries to use the CLI command if available, falls back to python3 + script path.
        """
        import shutil

        # Check if claude-board CLI is available in PATH
        if shutil.which("claude-board"):
            return f"claude-board hook {hook_type}"

        # Fallback to python3 + script path for development
        if hook_type == "permission":
            return f"python3 {self._get_hook_script_path()}"
        elif hook_type == "todo":
            return f"python3 {self._get_todo_hook_script_path()}"
        else:
            raise ValueError(f"Unknown hook type: {hook_type}")

    def _get_autostart_command(self) -> str:
        """
        Get the command to auto-start the server.

        Uses daemon mode and suppresses errors if already running.
        """
        import shutil

        # Check if claude-board CLI is available in PATH
        if shutil.which("claude-board"):
            return "claude-board serve --daemon 2>/dev/null || true"

        # Fallback: not available, skip auto-start
        return "true"

    def _create_our_hooks(self) -> dict[str, list[JsonDict]]:
        """Create our hook configurations"""
        permission_command = self._get_hook_command("permission")
        todo_command = self._get_hook_command("todo")
        autostart_command = self._get_autostart_command()

        return {
            "SessionStart": [{
                "matcher": ".*",
                "hooks": [{
                    "type": "command",
                    "command": autostart_command,
                    "timeout": 10
                }],
                HOOK_MARKER: True  # Marker to identify our hook
            }],
            "PermissionRequest": [{
                "matcher": ".*",
                "hooks": [{
                    "type": "command",
                    "command": permission_command,
                    "timeout": 60
                }],
                HOOK_MARKER: True  # Marker to identify our hook
            }],
            "PostToolUse": [{
                "matcher": "TodoWrite",
                "hooks": [{
                    "type": "command",
                    "command": todo_command,
                    "timeout": 5
                }],
                HOOK_MARKER: True
            }]
        }

    def install_hooks(self) -> bool:
        """
        Install our hooks while preserving user's existing hooks.

        Returns True if successful.
        """
        settings = self._load_settings()

        # Ensure hooks section exists
        if "hooks" not in settings:
            settings["hooks"] = {}

        our_hooks = self._create_our_hooks()

        for event_name, our_matchers in our_hooks.items():
            # Ensure event section exists
            if event_name not in settings["hooks"]:
                settings["hooks"][event_name] = []

            # Remove any existing hooks from us (by marker)
            settings["hooks"][event_name] = [
                h for h in settings["hooks"][event_name]
                if not h.get(HOOK_MARKER)
            ]

            # Add our hooks
            settings["hooks"][event_name].extend(our_matchers)

        self._save_settings(settings)
        return True

    def uninstall_hooks(self) -> bool:
        """
        Remove our hooks while preserving user's other hooks.

        Returns True if successful.
        """
        if not self.settings_file.exists():
            return True

        settings = self._load_settings()

        if "hooks" not in settings:
            return True

        # Remove our hooks from each event type
        for event_name in list(settings["hooks"].keys()):
            settings["hooks"][event_name] = [
                h for h in settings["hooks"][event_name]
                if not h.get(HOOK_MARKER)
            ]

            # Clean up empty event lists
            if not settings["hooks"][event_name]:
                del settings["hooks"][event_name]

        # Clean up empty hooks section
        if not settings["hooks"]:
            del settings["hooks"]

        self._save_settings(settings)
        return True

    def is_installed(self) -> bool:
        """Check if our hooks are currently installed"""
        settings = self._load_settings()

        if "hooks" not in settings:
            return False

        for event_name, matchers in settings["hooks"].items():
            for matcher in matchers:
                if matcher.get(HOOK_MARKER):
                    return True

        return False

    def get_hooks_status(self) -> HooksStatus:
        """Get detailed status of hooks installation"""
        settings = self._load_settings()

        our_hooks: list[InstalledHookInfo] = []
        other_hooks_count = 0
        installed = False

        hooks_section = settings.get("hooks")
        if isinstance(hooks_section, dict):
            for event_name, matchers in hooks_section.items():
                if not isinstance(matchers, list):
                    continue
                for matcher in matchers:
                    if not isinstance(matcher, dict):
                        continue
                    if matcher.get(HOOK_MARKER):
                        installed = True
                        matcher_value = matcher.get("matcher", "*")
                        our_hooks.append(
                            InstalledHookInfo(
                                event=str(event_name),
                                matcher=str(matcher_value) if matcher_value else "*",
                            )
                        )
                    else:
                        other_hooks_count += 1

        return HooksStatus(
            installed=installed,
            settings_file=str(self.settings_file),
            settings_exists=self.settings_file.exists(),
            our_hooks=our_hooks,
            other_hooks_count=other_hooks_count,
        )
