"""
Claude Board - Physical Console for Claude Code

A permission approval console that supports:
- Web UI for mobile/desktop approval
- Future: Bluetooth physical console with mechanical keys and e-ink display
"""

__app_name__ = "claude-board"

# Version is automatically set by hatch-vcs from git tags
try:
    from ._version import __version__
except ImportError:
    # Fallback for editable installs or when _version.py doesn't exist
    __version__ = "0.0.0.dev0"
