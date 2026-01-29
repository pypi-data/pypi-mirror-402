"""
Claude Board Chat Module

Provides PTY-based interactive Claude Code sessions with:
- Session persistence (attach/detach)
- Multi-project support
- Web UI integration for prompt input
- Real-time output streaming
"""

from .session import ChatSession, ChatSessionManager
from .terminal_client import TerminalClient

__all__ = [
    "ChatSession",
    "ChatSessionManager",
    "TerminalClient",
]
