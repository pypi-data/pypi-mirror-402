"""Unit tests for container operations."""

import json
from unittest.mock import Mock, patch

import pytest

from vllmoni.app.models import DockerInfo, EnvInfo, ModelInfo, UserInfo
from vllmoni.container.run import run
from vllmoni.container.stop import stop


def test_container_run_success():
    """Test successful container run."""
    model_info = ModelInfo(
        model_name="test-model",
        model_name_short="test",
        gpu_memory_utilization=0.9,
        max_model_len=4096,
    )
    env_info = EnvInfo(base_url="http://localhost:8000/v1/", port=8000, devices="0")
    user_info = UserInfo(user_name="testuser", user_id="1000", group_id="1000")

    with patch("vllmoni.container.run.subprocess.run") as mock_subprocess:
        # Set environment variables for the test
        import os

        os.environ["VLLM_API_KEY"] = "test_key"
        os.environ["HF_HOME"] = "/tmp/hf"
        os.environ["HUGGING_FACE_HUB_TOKEN"] = "test_token"

        # Mock docker run output
        mock_run_result = Mock()
        mock_run_result.stdout = "abc123def456"

        # Mock docker inspect output
        mock_inspect_result = Mock()
        inspect_data = {
            "Id": "abc123def456789012345678901234567890",
            "Name": "/vllmoni_test",
            "Config": {"Image": "vllm/vllm-openai:v0.9.1", "Labels": {}, "Env": []},
            "State": {"Status": "running"},
            "NetworkSettings": {"Ports": {"8000/tcp": []}},
        }
        mock_inspect_result.stdout = json.dumps([inspect_data])

        mock_subprocess.side_effect = [mock_run_result, mock_inspect_result]

        with patch("vllmoni.container.run.os.makedirs"):
            result = run(model_info, env_info, user_info)

        assert result is not None
        assert isinstance(result, DockerInfo)
        assert result.container_id == "abc123def456"
        assert result.image_name == "vllm/vllm-openai"


def test_container_run_missing_api_key(monkeypatch):
    """Test container run without VLLM_API_KEY."""
    monkeypatch.delenv("VLLM_API_KEY", raising=False)

    import os

    assert os.getenv("VLLM_API_KEY") is None

    model_info = ModelInfo(
        model_name="test-model",
        model_name_short="test",
        gpu_memory_utilization=0.9,
        max_model_len=4096,
    )
    env_info = EnvInfo(base_url="http://localhost:8000/v1/", port=8000, devices="0")
    user_info = UserInfo(user_name="testuser", user_id="1000", group_id="1000")

    # Mock subprocess and os.makedirs to avoid side effects
    with (
        patch("vllmoni.container.run.subprocess.run") as mock_subproc,
        patch("vllmoni.container.run.os.makedirs"),
    ):
        with pytest.raises(ValueError, match="VLLM_API_KEY"):
            run(model_info, env_info, user_info)
        mock_subproc.assert_not_called()


def test_container_run_docker_failure():
    """Test container run when docker command fails."""
    model_info = ModelInfo(
        model_name="test-model",
        model_name_short="test",
        gpu_memory_utilization=0.9,
        max_model_len=4096,
    )
    env_info = EnvInfo(base_url="http://localhost:8000/v1/", port=8000, devices="0")
    user_info = UserInfo(user_name="testuser", user_id="1000", group_id="1000")

    with patch("vllmoni.container.run.subprocess.run") as mock_subprocess:
        # Set environment variables for the test
        import os

        os.environ["VLLM_API_KEY"] = "test_key"
        os.environ["HF_HOME"] = "/tmp/hf"
        os.environ["HUGGING_FACE_HUB_TOKEN"] = "test_token"

        # Mock docker command failure
        import subprocess

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "docker run", stderr="Docker error")

        with patch("vllmoni.container.run.os.makedirs"):
            result = run(model_info, env_info, user_info)

        assert result is None


def test_container_stop_success():
    """Test successful container stop."""
    with patch("vllmoni.container.stop.subprocess.run") as mock_subprocess:
        result = stop("abc123")

        assert result is True
        # Should call both docker stop and docker rm
        assert mock_subprocess.call_count == 2


def test_container_stop_failure():
    """Test container stop failure."""
    with patch("vllmoni.container.stop.subprocess.run") as mock_subprocess:
        import subprocess

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "docker stop", stderr="Docker error")

        result = stop("abc123")

        assert result is False


def test_container_stop_nonexistent():
    """Test stopping a non-existent container."""
    with patch("vllmoni.container.stop.subprocess.run") as mock_subprocess:
        import subprocess

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "docker stop")

        result = stop("nonexistent")

        assert result is False
