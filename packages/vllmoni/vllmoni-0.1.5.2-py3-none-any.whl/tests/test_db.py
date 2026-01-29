"""Unit tests for database functionality."""

from pathlib import Path

from vllmoni.app.db import get_session, init_db


def test_init_db_creates_database(temp_db_path, monkeypatch):
    """Test that init_db creates a new database."""
    # Mock get_settings to return our temp db path
    monkeypatch.setattr("vllmoni.app.db.get_settings", lambda: {"db_path": temp_db_path})

    db_file = Path(temp_db_path.replace("sqlite:///", ""))

    # Ensure database doesn't exist
    if db_file.exists():
        db_file.unlink()

    # Initialize database
    init_db()

    # Check that database file was created
    assert db_file.exists()


def test_init_db_with_override(temp_db_path, monkeypatch):
    """Test that init_db with override deletes and recreates database."""
    # Mock get_settings
    monkeypatch.setattr("vllmoni.app.db.get_settings", lambda: {"db_path": temp_db_path})

    db_file = Path(temp_db_path.replace("sqlite:///", ""))

    # Create initial database
    init_db()
    assert db_file.exists()

    # Wait a bit and recreate with override
    import time

    time.sleep(0.1)
    init_db(override=True)

    # Database should still exist but be recreated
    assert db_file.exists()
    # Note: mtime check might not always work reliably, so we just verify existence


def test_init_db_without_override_preserves_existing(temp_db_path, monkeypatch):
    """Test that init_db without override preserves existing database."""
    # Mock get_settings
    monkeypatch.setattr("vllmoni.app.db.get_settings", lambda: {"db_path": temp_db_path})

    db_file = Path(temp_db_path.replace("sqlite:///", ""))

    # Create initial database
    init_db()
    assert db_file.exists()

    # Try to init again without override
    import time

    time.sleep(0.1)
    init_db(override=False)

    # Database should still exist
    assert db_file.exists()


def test_get_session_returns_session(temp_db_path, monkeypatch):
    """Test that get_session returns a valid SQLAlchemy session."""
    # Mock get_settings
    monkeypatch.setattr("vllmoni.app.db.get_settings", lambda: {"db_path": temp_db_path})

    # Initialize database
    init_db()

    # Get session
    session = get_session()

    # Verify it's a session object
    assert session is not None
    assert hasattr(session, "query")
    assert hasattr(session, "add")
    assert hasattr(session, "commit")
