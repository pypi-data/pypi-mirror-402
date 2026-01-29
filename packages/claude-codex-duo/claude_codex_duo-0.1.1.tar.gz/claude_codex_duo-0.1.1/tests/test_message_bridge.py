"""Tests for the message bridge."""

import tempfile
from pathlib import Path

import pytest

from claude_codex_duo import Message, MessageBridge, MessageType


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def bridge(temp_dir):
    """Create a message bridge with temp directory."""
    return MessageBridge("test_session", base_dir=temp_dir)


class TestMessageBridge:
    """Tests for MessageBridge class."""

    def test_init_creates_directories(self, bridge, temp_dir):
        """Test that initialization creates necessary directories."""
        session_dir = temp_dir / "sessions" / "test_session"
        assert session_dir.exists()
        assert (session_dir / "claude_inbox.json").exists()
        assert (session_dir / "codex_inbox.json").exists()

    def test_send_message_to_codex(self, bridge):
        """Test sending a message from Claude to Codex."""
        msg = Message(
            msg_type=MessageType.REVIEW_REQUEST,
            sender="claude",
            content="Please review this code",
            timestamp="2026-01-18T12:00:00",
        )
        bridge.send_message(msg)

        # Codex should receive the message
        messages = bridge.get_messages("codex")
        assert len(messages) == 1
        assert messages[0].sender == "claude"
        assert messages[0].content == "Please review this code"

    def test_send_message_to_claude(self, bridge):
        """Test sending a message from Codex to Claude."""
        msg = Message(
            msg_type=MessageType.REVIEW_RESPONSE,
            sender="codex",
            content="APPROVED - looks good!",
            timestamp="2026-01-18T12:00:00",
        )
        bridge.send_message(msg)

        # Claude should receive the message
        messages = bridge.get_messages("claude")
        assert len(messages) == 1
        assert messages[0].sender == "codex"

    def test_pop_message(self, bridge):
        """Test popping a message from inbox."""
        # Send two messages
        for i in range(2):
            msg = Message(
                msg_type=MessageType.STATUS_UPDATE,
                sender="claude",
                content=f"Message {i}",
                timestamp="2026-01-18T12:00:00",
            )
            bridge.send_message(msg)

        # Pop first message
        first = bridge.pop_message("codex")
        assert first.content == "Message 0"

        # Pop second message
        second = bridge.pop_message("codex")
        assert second.content == "Message 1"

        # No more messages
        third = bridge.pop_message("codex")
        assert third is None

    def test_clear_inbox(self, bridge):
        """Test clearing an inbox."""
        msg = Message(
            msg_type=MessageType.STATUS_UPDATE,
            sender="claude",
            content="Test",
            timestamp="2026-01-18T12:00:00",
        )
        bridge.send_message(msg)

        assert len(bridge.get_messages("codex")) == 1

        bridge.clear_inbox("codex")
        assert len(bridge.get_messages("codex")) == 0

    def test_request_review(self, bridge):
        """Test the request_review convenience method."""
        bridge.request_review(
            content="def hello(): pass",
            files=["main.py"],
            summary="Added hello function"
        )

        messages = bridge.get_messages("codex")
        assert len(messages) == 1
        assert messages[0].msg_type == MessageType.REVIEW_REQUEST
        assert messages[0].metadata["files"] == ["main.py"]

    def test_send_review(self, bridge):
        """Test the send_review convenience method."""
        bridge.send_review(
            verdict="APPROVED",
            feedback="Great work!",
            issues=[]
        )

        messages = bridge.get_messages("claude")
        assert len(messages) == 1
        assert messages[0].msg_type == MessageType.REVIEW_RESPONSE
        assert messages[0].metadata["verdict"] == "APPROVED"

    def test_conversation_history(self, bridge):
        """Test that conversation history is logged."""
        msg = Message(
            msg_type=MessageType.STATUS_UPDATE,
            sender="claude",
            content="Test message",
            timestamp="2026-01-18T12:00:00",
        )
        bridge.send_message(msg)

        history = bridge.get_conversation_history()
        assert len(history) == 1
        assert history[0]["content"] == "Test message"


class TestMessage:
    """Tests for Message dataclass."""

    def test_to_dict(self):
        """Test serializing a message to dict."""
        msg = Message(
            msg_type=MessageType.REVIEW_REQUEST,
            sender="claude",
            content="Review this",
            timestamp="2026-01-18T12:00:00",
            metadata={"key": "value"},
        )
        data = msg.to_dict()

        assert data["msg_type"] == "review_request"
        assert data["sender"] == "claude"
        assert data["content"] == "Review this"
        assert data["metadata"] == {"key": "value"}

    def test_from_dict(self):
        """Test deserializing a message from dict."""
        data = {
            "msg_type": "review_response",
            "sender": "codex",
            "content": "APPROVED",
            "timestamp": "2026-01-18T12:00:00",
            "metadata": {"verdict": "APPROVED"},
        }
        msg = Message.from_dict(data)

        assert msg.msg_type == MessageType.REVIEW_RESPONSE
        assert msg.sender == "codex"
        assert msg.content == "APPROVED"
