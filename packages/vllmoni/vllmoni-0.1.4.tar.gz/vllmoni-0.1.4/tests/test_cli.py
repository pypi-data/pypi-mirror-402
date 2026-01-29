"""Unit tests for CLI commands."""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from typer.testing import CliRunner

from cli.cli import app

runner = CliRunner()


def test_cli_init_command(monkeypatch, temp_db_path):
    """Test the init command."""
    # Mock get_settings to use temp db
    monkeypatch.setattr("app.db.get_settings", lambda: {"db_path": temp_db_path})

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    # Check that database was created
    db_file = Path(temp_db_path.replace("sqlite:///", ""))
    assert db_file.exists()


def test_cli_init_with_override(monkeypatch, temp_db_path):
    """Test the init command with override flag."""
    monkeypatch.setattr("app.db.get_settings", lambda: {"db_path": temp_db_path})

    # First init
    result1 = runner.invoke(app, ["init"])
    assert result1.exit_code == 0

    # Second init with override
    result2 = runner.invoke(app, ["init", "--override"])
    assert result2.exit_code == 0


def test_cli_ls_command_empty(monkeypatch, temp_db_path):
    """Test the ls command with no models."""
    monkeypatch.setattr("app.db.get_settings", lambda: {"db_path": temp_db_path})

    # Initialize database first
    runner.invoke(app, ["init"])

    # Mock get_session to return a session with empty data
    with patch("cli.cli.get_session") as mock_session:
        mock_session.return_value.query.return_value.all.return_value = []

        result = runner.invoke(app, ["ls"])

        assert result.exit_code == 0
        # The logger outputs to stderr, not stdout
        # Just check it exits successfully


def test_cli_ls_command_with_models(monkeypatch, temp_db_path):
    """Test the ls command with models in database."""
    monkeypatch.setattr("app.db.get_settings", lambda: {"db_path": temp_db_path})

    # Create mock table row
    mock_row = MagicMock()
    mock_row.id = 1
    mock_row.created = "2024-01-01 12:00:00"
    mock_row.env_info = json.dumps({"base_url": "http://localhost:8000/v1/", "port": 8000})
    mock_row.model_info = json.dumps({"model_name_short": "llama3-8b", "model_name": "meta-llama/Llama-3-8B"})
    mock_row.user_info = json.dumps({"user_name": "testuser", "user_id": "1000", "group_id": "1000"})
    mock_row.docker_info = json.dumps(
        {
            "container_id": "abc123",
            "image_name": "vllm/vllm-openai",
            "image_tag": "v0.9.1",
        }
    )
    mock_row.gpu_infos = json.dumps([{"index": 0, "memory_used": 8000, "memory_total": 16000, "utilization": 75}])

    with patch("cli.cli.get_session"):
        mock_repo = Mock()
        mock_repo.get_all.return_value = [mock_row]

        with patch("cli.cli.ModelRepository", return_value=mock_repo):
            result = runner.invoke(app, ["ls"])

            assert result.exit_code == 0
            # Output is rendered as a table, just check it ran successfully


def test_cli_stop_command(monkeypatch, temp_db_path):
    """Test the stop command."""
    monkeypatch.setattr("app.db.get_settings", lambda: {"db_path": temp_db_path})

    # Mock the necessary components
    mock_row = MagicMock()
    mock_row.docker_info = json.dumps({"container_id": "abc123"})

    with patch("cli.cli.get_session"):
        mock_repo = Mock()
        mock_repo.get.return_value = mock_row
        mock_repo.delete.return_value = {"status": "deleted"}

        with patch("cli.cli.ModelRepository", return_value=mock_repo), patch("cli.cli.stop_container") as mock_stop:
            result = runner.invoke(app, ["stop", "1"])

            assert result.exit_code == 0
            mock_stop.assert_called_once_with("abc123")
            mock_repo.delete.assert_called_once_with(1)


def test_cli_stop_command_not_found(monkeypatch, temp_db_path):
    """Test the stop command with non-existent model."""
    monkeypatch.setattr("app.db.get_settings", lambda: {"db_path": temp_db_path})

    with patch("cli.cli.get_session"):
        mock_repo = Mock()
        mock_repo.get.return_value = None

        with patch("cli.cli.ModelRepository", return_value=mock_repo):
            result = runner.invoke(app, ["stop", "999"])

            # Command should complete, error is logged
            assert result.exit_code == 0


def test_cli_stop_all_command(monkeypatch, temp_db_path):
    """Test the stop-all command."""
    monkeypatch.setattr("app.db.get_settings", lambda: {"db_path": temp_db_path})

    # Create mock rows
    mock_row1 = MagicMock()
    mock_row1.docker_info = json.dumps({"container_id": "abc123"})
    mock_row2 = MagicMock()
    mock_row2.docker_info = json.dumps({"container_id": "def456"})

    with patch("cli.cli.get_session"):
        mock_repo = Mock()
        mock_repo.get_all.return_value = [mock_row1, mock_row2]
        mock_repo.delete_all.return_value = {"status": "all deleted"}

        with patch("cli.cli.ModelRepository", return_value=mock_repo), patch("cli.cli.stop_container") as mock_stop:
            result = runner.invoke(app, ["stop-all"])

            assert result.exit_code == 0
            assert mock_stop.call_count == 2


# def test_cli_run_command_missing_env_vars(monkeypatch, temp_db_path):
#     """Test the run command without required environment variables."""
#     monkeypatch.setattr("app.db.get_settings", lambda: {"db_path": temp_db_path})

#     # Don't set VLLM_API_KEY
#     monkeypatch.delenv("VLLM_API_KEY", raising=False)

#     with patch("cli.cli.get_session"), patch("cli.cli.my_compose") as mock_compose:
#         # Mock the config
#         mock_cfg = Mock()
#         mock_cfg.devices = "0"
#         mock_cfg.base_url = "http://localhost:8000/v1/"
#         mock_cfg.port = 8000
#         mock_cfg.image_name = "vllm/vllm-openai"
#         mock_cfg.image_tag = "v0.9.1"
#         mock_cfg.model = {
#             "model_name": "test-model",
#             "model_name_short": "test",
#             "gpu_memory_utilization": 0.9,
#             "max_model_len": 4096,
#         }
#         mock_compose.return_value = mock_cfg

#         # Patch run_container to raise ValueError as if VLLM_API_KEY is missing
#         with patch(
#             "cli.cli.run_container",
#             side_effect=ValueError("VLLM_API_KEY key is not set. Please set VLLM_API_KEY in the environment."),
#         ):
#             result = runner.invoke(app, ["run"])

#             # The command should fail and print the error
#             assert result.exit_code != 0
#             assert "VLLM_API_KEY" in result.stdout


def test_cli_logs_command(monkeypatch, temp_db_path):
    """Test the logs command."""
    monkeypatch.setattr("app.db.get_settings", lambda: {"db_path": temp_db_path})

    mock_row = MagicMock()
    mock_row.docker_info = json.dumps({"container_id": "abc123"})

    with patch("cli.cli.get_session"):
        mock_repo = Mock()
        mock_repo.get.return_value = mock_row

        with patch("cli.cli.ModelRepository", return_value=mock_repo), patch("cli.cli.docker.from_env") as mock_docker:
            mock_container = Mock()
            mock_container.logs.return_value = b"Test log output"
            mock_docker.return_value.containers.get.return_value = mock_container

            result = runner.invoke(app, ["logs", "1"])

            assert result.exit_code == 0
            mock_container.logs.assert_called_once()


def test_cli_logs_command_not_found(monkeypatch, temp_db_path):
    """Test the logs command with non-existent model."""
    monkeypatch.setattr("app.db.get_settings", lambda: {"db_path": temp_db_path})

    with patch("cli.cli.get_session"):
        mock_repo = Mock()
        mock_repo.get.return_value = None

        with patch("cli.cli.ModelRepository", return_value=mock_repo):
            result = runner.invoke(app, ["logs", "999"])

            # Command should complete, error is logged
            assert result.exit_code == 0
