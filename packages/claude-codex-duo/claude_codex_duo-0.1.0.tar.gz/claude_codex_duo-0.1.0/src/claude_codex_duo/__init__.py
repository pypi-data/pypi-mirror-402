"""
Claude-Codex Bridge: Duo Peer Programming

A simple library for peer programming between Claude Code and Codex.
Claude codes, Codex reviews, until consensus is reached.

Usage:
    from claude_codex_duo import DuoSession, create_session

    # Create a new session
    session = create_session("my_task", "Implement user login")

    # Submit code for review
    session.submit_code("def login(user, password): ...")

    # Wait for Codex's review
    exchange = session.wait_for_review()

    if session.has_consensus:
        print("Approved!")
"""

__version__ = "0.1.0"

from .duo_session import (
    DuoSession,
    Exchange,
    SessionStatus,
    Verdict,
    create_session,
    load_session,
)
from .message_bridge import (
    Message,
    MessageBridge,
    MessageType,
    get_data_dir,
)
from .providers import ClaudeProvider, CodexProvider

__all__ = [
    # Main classes
    "DuoSession",
    "MessageBridge",
    # Session helpers
    "create_session",
    "load_session",
    # Types
    "SessionStatus",
    "Verdict",
    "Exchange",
    "Message",
    "MessageType",
    # Providers
    "ClaudeProvider",
    "CodexProvider",
    # Utilities
    "get_data_dir",
]
