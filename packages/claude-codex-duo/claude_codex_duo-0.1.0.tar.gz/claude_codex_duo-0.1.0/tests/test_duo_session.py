"""Tests for the duo session manager."""

import tempfile
from pathlib import Path

import pytest

from claude_codex_duo import (
    DuoSession,
    SessionStatus,
    Verdict,
    create_session,
    load_session,
)


@pytest.fixture
def temp_data_dir(monkeypatch):
    """Set up a temporary data directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("CLAUDE_CODEX_DUO_DATA", tmpdir)
        yield Path(tmpdir)


class TestDuoSession:
    """Tests for DuoSession class."""

    def test_create_session(self, temp_data_dir):
        """Test creating a new session."""
        session = create_session(
            "test_session",
            "Write a hello world function",
            max_rounds=5
        )

        assert session.session_id == "test_session"
        assert session.task_description == "Write a hello world function"
        assert session.max_rounds == 5
        assert session.current_round == 0
        assert session.status == SessionStatus.ACTIVE

    def test_submit_code(self, temp_data_dir):
        """Test submitting code for review."""
        session = create_session("test_submit", "Test task")

        exchange = session.submit_code(
            "def hello(): return 'world'",
            files_modified=["main.py"]
        )

        assert session.current_round == 1
        assert session.status == SessionStatus.REVIEWING
        assert len(session.exchanges) == 1
        assert exchange.claude_submission == "def hello(): return 'world'"
        assert exchange.files_modified == ["main.py"]

    def test_submit_review(self, temp_data_dir):
        """Test submitting a review response."""
        session = create_session("test_review", "Test task")
        session.submit_code("def test(): pass")

        session.submit_review(
            Verdict.APPROVED,
            "Looks good!",
            issues=[]
        )

        assert session.status == SessionStatus.CONSENSUS
        assert session.exchanges[-1].verdict == Verdict.APPROVED
        assert session.exchanges[-1].codex_review == "Looks good!"

    def test_needs_changes_keeps_session_active(self, temp_data_dir):
        """Test that NEEDS_CHANGES keeps session active."""
        session = create_session("test_changes", "Test task")
        session.submit_code("def buggy(): pass")

        session.submit_review(
            Verdict.NEEDS_CHANGES,
            "Found bugs",
            issues=["Bug 1", "Bug 2"]
        )

        assert session.status == SessionStatus.ACTIVE
        assert not session.has_consensus

    def test_max_rounds_reached(self, temp_data_dir):
        """Test that session ends after max rounds."""
        session = create_session("test_max", "Test task", max_rounds=2)

        # Round 1
        session.submit_code("attempt 1")
        session.submit_review(Verdict.NEEDS_CHANGES, "Try again")

        # Round 2
        session.submit_code("attempt 2")
        session.submit_review(Verdict.NEEDS_CHANGES, "Still not right")

        assert session.status == SessionStatus.MAX_ROUNDS
        assert session.is_complete
        assert not session.has_consensus

    def test_save_and_load(self, temp_data_dir):
        """Test saving and loading a session."""
        # Create and save
        session = create_session("test_persist", "Persistence test")
        session.submit_code("def persist(): pass")

        # Load
        loaded = load_session("test_persist")

        assert loaded.session_id == "test_persist"
        assert loaded.task_description == "Persistence test"
        assert len(loaded.exchanges) == 1
        assert loaded.exchanges[0].claude_submission == "def persist(): pass"

    def test_is_complete_property(self, temp_data_dir):
        """Test the is_complete property."""
        session = create_session("test_complete", "Test")

        assert not session.is_complete

        session.submit_code("code")
        session.submit_review(Verdict.APPROVED, "Good")

        assert session.is_complete

    def test_has_consensus_property(self, temp_data_dir):
        """Test the has_consensus property."""
        session = create_session("test_consensus", "Test")

        assert not session.has_consensus

        session.submit_code("code")
        session.submit_review(Verdict.APPROVED, "Good")

        assert session.has_consensus

    def test_get_latest_exchange(self, temp_data_dir):
        """Test getting the latest exchange."""
        session = create_session("test_latest", "Test")

        assert session.get_latest_exchange() is None

        session.submit_code("first")
        session.submit_review(Verdict.NEEDS_CHANGES, "nope")

        session.submit_code("second")

        latest = session.get_latest_exchange()
        assert latest.claude_submission == "second"


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_create_session_function(self, temp_data_dir):
        """Test the create_session convenience function."""
        session = create_session("convenience_test", "Quick test")

        assert isinstance(session, DuoSession)
        assert session.session_id == "convenience_test"

    def test_load_session_not_found(self, temp_data_dir):
        """Test loading a non-existent session."""
        with pytest.raises(FileNotFoundError):
            load_session("does_not_exist")
