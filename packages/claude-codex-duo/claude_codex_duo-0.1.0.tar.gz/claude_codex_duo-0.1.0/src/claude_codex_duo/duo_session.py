"""
Duo Peer Programming Session Manager

Manages a 2-way peer programming session between Claude and Codex.
Claude codes, Codex reviews, until consensus is reached.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from .message_bridge import Message, MessageBridge, get_data_dir


class SessionStatus(str, Enum):
    """Status of a peer programming session."""
    ACTIVE = "active"
    REVIEWING = "reviewing"
    CONSENSUS = "consensus"
    MAX_ROUNDS = "max_rounds_reached"
    CANCELLED = "cancelled"


class Verdict(str, Enum):
    """Review verdict from Codex."""
    APPROVED = "approved"
    NEEDS_CHANGES = "needs_changes"
    DISCUSS = "discuss"


@dataclass
class Exchange:
    """A single round of code submission and review."""
    round_num: int
    timestamp: str
    claude_submission: str
    codex_review: Optional[str] = None
    verdict: Optional[Verdict] = None
    files_modified: list[str] = field(default_factory=list)


@dataclass
class DuoSession:
    """
    A duo peer programming session between Claude and Codex.

    Usage:
        session = DuoSession.create("my_task", "Implement user authentication")
        session.submit_code("def authenticate(user, password): ...")
        review = session.wait_for_review()
        if review.verdict == Verdict.APPROVED:
            print("Consensus reached!")
    """
    session_id: str
    task_description: str
    max_rounds: int = 10
    current_round: int = 0
    exchanges: list[Exchange] = field(default_factory=list)
    status: SessionStatus = SessionStatus.ACTIVE
    workspace: Optional[str] = None

    _bridge: Optional[MessageBridge] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize the message bridge."""
        if self._bridge is None:
            self._bridge = MessageBridge(self.session_id)

    @classmethod
    def create(
        cls,
        session_id: str,
        task_description: str,
        workspace: str = None,
        max_rounds: int = 10
    ) -> "DuoSession":
        """
        Create a new duo peer programming session.

        Args:
            session_id: Unique identifier for this session
            task_description: What Claude and Codex are working on
            workspace: Optional working directory path
            max_rounds: Maximum review rounds before giving up

        Returns:
            New DuoSession instance
        """
        session = cls(
            session_id=session_id,
            task_description=task_description,
            max_rounds=max_rounds,
            workspace=workspace,
        )
        session.save()
        return session

    @classmethod
    def load(cls, session_id: str) -> "DuoSession":
        """Load an existing session from disk."""
        session_file = get_data_dir() / "sessions" / session_id / "session.json"
        if not session_file.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")

        data = json.loads(session_file.read_text())
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> "DuoSession":
        """Deserialize session from dict."""
        session = cls(
            session_id=data["session_id"],
            task_description=data["task_description"],
            max_rounds=data["max_rounds"],
            current_round=data["current_round"],
            status=SessionStatus(data["status"]),
            workspace=data.get("workspace"),
        )
        session.exchanges = [
            Exchange(
                round_num=e["round_num"],
                timestamp=e["timestamp"],
                claude_submission=e["claude_submission"],
                codex_review=e.get("codex_review"),
                verdict=Verdict(e["verdict"]) if e.get("verdict") else None,
                files_modified=e.get("files_modified", []),
            )
            for e in data.get("exchanges", [])
        ]
        return session

    def to_dict(self) -> dict:
        """Serialize session to dict."""
        return {
            "session_id": self.session_id,
            "task_description": self.task_description,
            "max_rounds": self.max_rounds,
            "current_round": self.current_round,
            "status": self.status.value,
            "workspace": self.workspace,
            "exchanges": [
                {
                    "round_num": e.round_num,
                    "timestamp": e.timestamp,
                    "claude_submission": e.claude_submission,
                    "codex_review": e.codex_review,
                    "verdict": e.verdict.value if e.verdict else None,
                    "files_modified": e.files_modified,
                }
                for e in self.exchanges
            ],
        }

    def save(self) -> None:
        """Save session state to disk."""
        session_file = self._bridge.get_session_dir() / "session.json"
        session_file.write_text(json.dumps(self.to_dict(), indent=2))

    def submit_code(
        self,
        content: str,
        files_modified: list[str] = None,
        summary: str = ""
    ) -> Exchange:
        """
        Submit code from Claude for Codex review.

        Args:
            content: The code or changes to review
            files_modified: List of files that were modified
            summary: Brief summary of what was done

        Returns:
            The exchange record
        """
        if self.status not in (SessionStatus.ACTIVE, SessionStatus.REVIEWING):
            raise RuntimeError(f"Cannot submit code in status: {self.status}")

        self.current_round += 1
        exchange = Exchange(
            round_num=self.current_round,
            timestamp=datetime.now().isoformat(),
            claude_submission=content,
            files_modified=files_modified or [],
        )
        self.exchanges.append(exchange)
        self.status = SessionStatus.REVIEWING

        # Send to Codex via message bridge
        self._bridge.request_review(content, files_modified, summary)
        self.save()

        return exchange

    def submit_review(
        self,
        verdict: Verdict,
        feedback: str,
        issues: list[str] = None
    ) -> None:
        """
        Submit review from Codex.

        Args:
            verdict: APPROVED, NEEDS_CHANGES, or DISCUSS
            feedback: Detailed review feedback
            issues: Specific issues found
        """
        if not self.exchanges:
            raise RuntimeError("No code submitted to review")

        exchange = self.exchanges[-1]
        exchange.codex_review = feedback
        exchange.verdict = verdict

        # Check for consensus
        if verdict == Verdict.APPROVED:
            self.status = SessionStatus.CONSENSUS
        elif self.current_round >= self.max_rounds:
            self.status = SessionStatus.MAX_ROUNDS
        else:
            self.status = SessionStatus.ACTIVE

        # Send response via message bridge
        self._bridge.send_review(verdict.value.upper(), feedback, issues)
        self.save()

    def wait_for_review(self, timeout: int = 300) -> Optional[Exchange]:
        """
        Wait for Codex's review response.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            The exchange with review, or None if timeout
        """
        msg = self._bridge.wait_for_message("claude", timeout=timeout)
        if msg is None:
            return None

        # Update current exchange with review
        if self.exchanges:
            exchange = self.exchanges[-1]
            exchange.codex_review = msg.content
            verdict_str = msg.metadata.get("verdict", "").lower()
            if verdict_str in ("approved", "lgtm", "looks good"):
                exchange.verdict = Verdict.APPROVED
                self.status = SessionStatus.CONSENSUS
            elif verdict_str in ("needs_changes", "changes required"):
                exchange.verdict = Verdict.NEEDS_CHANGES
            else:
                exchange.verdict = Verdict.DISCUSS
            self.save()
            return exchange

        return None

    def wait_for_submission(self, timeout: int = 300) -> Optional[Message]:
        """
        Wait for Claude's code submission (for Codex side).

        Args:
            timeout: Maximum seconds to wait

        Returns:
            The submission message, or None if timeout
        """
        return self._bridge.wait_for_message("codex", timeout=timeout)

    @property
    def is_complete(self) -> bool:
        """Check if session has reached consensus or max rounds."""
        return self.status in (SessionStatus.CONSENSUS, SessionStatus.MAX_ROUNDS)

    @property
    def has_consensus(self) -> bool:
        """Check if consensus was reached."""
        return self.status == SessionStatus.CONSENSUS

    def get_latest_exchange(self) -> Optional[Exchange]:
        """Get the most recent exchange."""
        return self.exchanges[-1] if self.exchanges else None

    def get_history(self) -> list[dict]:
        """Get full conversation history from message bridge."""
        return self._bridge.get_conversation_history()


def create_session(
    session_id: str,
    task: str,
    workspace: str = None,
    max_rounds: int = 10
) -> DuoSession:
    """
    Convenience function to create a new duo session.

    Args:
        session_id: Unique session identifier
        task: Task description
        workspace: Optional working directory
        max_rounds: Maximum review rounds

    Returns:
        New DuoSession
    """
    return DuoSession.create(session_id, task, workspace, max_rounds)


def load_session(session_id: str) -> DuoSession:
    """
    Convenience function to load an existing session.

    Args:
        session_id: Session identifier to load

    Returns:
        Loaded DuoSession
    """
    return DuoSession.load(session_id)
