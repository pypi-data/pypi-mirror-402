"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from vllmoni.app.models import Base


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(engine)
        session_local = sessionmaker(bind=engine)
        yield session_local()
        Base.metadata.drop_all(engine)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", "test_token")
    monkeypatch.setenv("VLLM_API_KEY", "test_api_key")
    monkeypatch.setenv("HF_HOME", "/tmp/test_hf_home")


@pytest.fixture
def temp_db_path():
    """Provide a temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_vllmoni.db"
        yield f"sqlite:///{db_path}"
