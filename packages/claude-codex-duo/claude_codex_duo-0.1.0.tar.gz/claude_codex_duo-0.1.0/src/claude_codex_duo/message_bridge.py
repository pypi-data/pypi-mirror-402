"""
Message Bridge for Claude-Codex Communication

File-based messaging with atomic locking for process-safe IPC.
No database required - just the filesystem.
"""

import fcntl
import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


def get_data_dir() -> Path:
    """Get the duo data directory.

    Priority:
    1. CLAUDE_CODEX_DUO_DATA env var
    2. ~/.claude-codex-duo/
    """
    if data_dir := os.environ.get("CLAUDE_CODEX_DUO_DATA"):
        return Path(data_dir)
    return Path.home() / ".claude-codex-duo"


@contextmanager
def locked_file(filepath: Path, mode: str = "r+"):
    """
    Context manager for atomic file operations with file locking.

    Uses fcntl.flock() for process-safe file locking on Unix.
    This ensures that only one process can read/write at a time,
    preventing race conditions between Claude and Codex.
    """
    # Ensure file exists for r+ mode
    if mode == "r+" and not filepath.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text("[]")

    with open(filepath, mode) as f:
        try:
            # Acquire exclusive lock (blocks until available)
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            yield f
        finally:
            # Release lock
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


class MessageType(str, Enum):
    """Types of messages exchanged between Claude and Codex."""
    REVIEW_REQUEST = "review_request"
    REVIEW_RESPONSE = "review_response"
    STATUS_UPDATE = "status_update"
    TASK_COMPLETE = "task_complete"
    ERROR = "error"


@dataclass
class Message:
    """A message exchanged between Claude and Codex."""
    msg_type: MessageType
    sender: str  # "claude" or "codex"
    content: str
    timestamp: str
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "msg_type": self.msg_type.value,
            "sender": self.sender,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            msg_type=MessageType(data["msg_type"]),
            sender=data["sender"],
            content=data["content"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata")
        )


class MessageBridge:
    """
    File-based message bridge for Claude-Codex communication.

    Each agent has an inbox file. Messages are written to the
    recipient's inbox and read from your own inbox.

    Thread-safe via fcntl file locking.
    """

    def __init__(self, session_id: str, base_dir: Path = None):
        """
        Initialize a message bridge for a session.

        Args:
            session_id: Unique identifier for this peer programming session
            base_dir: Optional base directory (defaults to ~/.claude-codex-bridge/)
        """
        self.session_id = session_id
        self.base_dir = base_dir or get_data_dir()
        self.messages_dir = self.base_dir / "sessions" / session_id
        self.messages_dir.mkdir(parents=True, exist_ok=True)

        # Message queues (files)
        self.claude_inbox = self.messages_dir / "claude_inbox.json"
        self.codex_inbox = self.messages_dir / "codex_inbox.json"
        self.conversation_log = self.messages_dir / "conversation.jsonl"

        # Initialize empty inboxes
        for inbox in [self.claude_inbox, self.codex_inbox]:
            if not inbox.exists():
                inbox.write_text("[]")

    def send_message(self, msg: Message) -> None:
        """
        Send a message to the other agent (thread-safe).

        Messages from Claude go to Codex's inbox and vice versa.
        """
        # Determine recipient inbox
        inbox = self.codex_inbox if msg.sender == "claude" else self.claude_inbox

        # Add to inbox with file locking
        with locked_file(inbox, "r+") as f:
            messages = json.load(f)
            messages.append(msg.to_dict())
            f.seek(0)
            f.truncate()
            json.dump(messages, f, indent=2)

        # Log to conversation (append-only)
        with open(self.conversation_log, "a") as f:
            f.write(json.dumps(msg.to_dict()) + "\n")

    def get_messages(self, recipient: str) -> list[Message]:
        """Get all pending messages for recipient (thread-safe)."""
        inbox = self.claude_inbox if recipient == "claude" else self.codex_inbox

        with locked_file(inbox, "r+") as f:
            messages = json.load(f)
        return [Message.from_dict(m) for m in messages]

    def pop_message(self, recipient: str) -> Optional[Message]:
        """Pop the oldest message from inbox (thread-safe)."""
        inbox = self.claude_inbox if recipient == "claude" else self.codex_inbox

        with locked_file(inbox, "r+") as f:
            messages = json.load(f)
            if not messages:
                return None
            msg_data = messages.pop(0)
            f.seek(0)
            f.truncate()
            json.dump(messages, f, indent=2)
            return Message.from_dict(msg_data)

    def clear_inbox(self, recipient: str) -> None:
        """Clear all messages from inbox (thread-safe)."""
        inbox = self.claude_inbox if recipient == "claude" else self.codex_inbox
        with locked_file(inbox, "r+") as f:
            f.seek(0)
            f.truncate()
            f.write("[]")

    def wait_for_message(
        self,
        recipient: str,
        timeout: int = 300,
        poll_interval: float = 2.0
    ) -> Optional[Message]:
        """
        Wait for a message with timeout.

        Args:
            recipient: "claude" or "codex"
            timeout: Maximum seconds to wait
            poll_interval: Seconds between checks

        Returns:
            Message if received, None if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            msg = self.pop_message(recipient)
            if msg:
                return msg
            time.sleep(poll_interval)
        return None

    def request_review(
        self,
        content: str,
        files: list[str] = None,
        summary: str = ""
    ) -> None:
        """
        Claude requests a code review from Codex.

        Args:
            content: The code or changes to review
            files: List of files modified
            summary: Brief summary of changes
        """
        msg = Message(
            msg_type=MessageType.REVIEW_REQUEST,
            sender="claude",
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata={
                "summary": summary,
                "files": files or []
            }
        )
        self.send_message(msg)

    def send_review(
        self,
        verdict: str,
        feedback: str,
        issues: list[str] = None
    ) -> None:
        """
        Codex sends review response.

        Args:
            verdict: "APPROVED" or "NEEDS_CHANGES"
            feedback: Detailed review feedback
            issues: List of specific issues found
        """
        msg = Message(
            msg_type=MessageType.REVIEW_RESPONSE,
            sender="codex",
            content=feedback,
            timestamp=datetime.now().isoformat(),
            metadata={
                "verdict": verdict,
                "issues": issues or []
            }
        )
        self.send_message(msg)

    def get_session_dir(self) -> Path:
        """Get the session directory path."""
        return self.messages_dir

    def get_conversation_history(self) -> list[dict]:
        """Read full conversation history from log."""
        if not self.conversation_log.exists():
            return []

        history = []
        with open(self.conversation_log) as f:
            for line in f:
                if line.strip():
                    history.append(json.loads(line))
        return history
