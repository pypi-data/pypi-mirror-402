"""Unit tests for data models."""

import json
import os
from dataclasses import asdict
from unittest.mock import patch

from app.models import (
    DockerInfo,
    EnvInfo,
    GPUInfo,
    ModelInfo,
    UserInfo,
)


def test_env_info_creation():
    """Test EnvInfo dataclass creation."""
    env = EnvInfo(base_url="http://localhost:8000/v1/", port=8000, devices="0,1")

    assert env.base_url == "http://localhost:8000/v1/"
    assert env.port == 8000
    assert env.devices == "0,1"
    assert env.image_name == "vllm/vllm-openai"
    assert env.image_tag == "v0.9.1"


def test_env_info_defaults():
    """Test EnvInfo default values."""
    env = EnvInfo(base_url="http://localhost:8000/v1/", port=8000)

    assert env.devices is None
    assert env.image_name == "vllm/vllm-openai"


def test_model_info_creation():
    """Test ModelInfo dataclass creation."""
    model = ModelInfo(
        model_name="meta-llama/Llama-3-8B",
        model_name_short="llama3-8b",
        gpu_memory_utilization=0.9,
        max_model_len=4096,
    )

    assert model.model_name == "meta-llama/Llama-3-8B"
    assert model.model_name_short == "llama3-8b"
    assert model.gpu_memory_utilization == 0.9
    assert model.max_model_len == 4096
    assert model.top_p == 0.95  # default
    assert model.tensor_parallel_size == 1  # default
    assert model.id is not None  # auto-generated UUID


def test_model_info_with_optional_params():
    """Test ModelInfo with optional parameters."""
    model = ModelInfo(
        model_name="test-model",
        model_name_short="test",
        gpu_memory_utilization=0.8,
        max_model_len=2048,
        enforce_eager=True,
        quantization="awq",
        tool_call_parser="mistral",
        tokenizer="custom-tokenizer",
        trust_remote_code=True,
        disable_log_requests=True,
        seed=42,
    )

    assert model.enforce_eager is True
    assert model.quantization == "awq"
    assert model.tool_call_parser == "mistral"
    assert model.tokenizer == "custom-tokenizer"
    assert model.trust_remote_code is True
    assert model.disable_log_requests is True
    assert model.seed == 42


def test_user_info_from_current_user():
    """Test UserInfo.from_current_user method."""
    with patch("app.models.os.getlogin", return_value="testuser"):
        user = UserInfo.from_current_user()

        assert user.user_name is not None
        assert user.user_id is not None
        assert user.group_id is not None
        assert user.user_name == "testuser"
        assert user.user_id == str(os.getuid())
        assert user.group_id == str(os.getgid())


def test_user_info_manual_creation():
    """Test manual UserInfo creation."""
    user = UserInfo(user_name="testuser", user_id="1000", user_role="admin", group_id="1000")

    assert user.user_name == "testuser"
    assert user.user_id == "1000"
    assert user.user_role == "admin"
    assert user.group_id == "1000"


def test_docker_info_from_inspect_data():
    """Test DockerInfo.from_inspect_data method."""
    inspect_data = {
        "Id": "abc123def456789012345678901234567890",
        "Name": "/vllmoni_testuser_llama3",
        "Config": {
            "Image": "vllm/vllm-openai:v0.9.1",
            "Labels": {"org.opencontainers.image.version": "0.9.1"},
            "Env": ["PATH=/usr/bin", "HOME=/root"],
        },
        "State": {"Status": "running"},
        "NetworkSettings": {"Ports": {"8000/tcp": [{"HostPort": "8000"}]}},
    }

    docker_info = DockerInfo.from_inspect_data(inspect_data, "0,1")

    assert docker_info.container_id == "abc123def456"  # First 12 chars
    assert docker_info.container_name == "vllmoni_testuser_llama3"
    assert docker_info.image_name == "vllm/vllm-openai"
    assert docker_info.image_tag == "v0.9.1"
    assert docker_info.docker_status == "running"
    assert docker_info.vllm_status == "starting"  # Default value on creation
    assert docker_info.docker_version == "0.9.1"
    assert docker_info.devices == "0,1"
    assert len(docker_info.env) == 2


def test_docker_info_manual_creation():
    """Test manual DockerInfo creation."""
    docker_info = DockerInfo(
        container_id="abc123",
        container_name="test_container",
        image_name="vllm/vllm-openai",
        image_tag="v0.9.1",
        docker_port="8000/tcp",
        devices="0",
    )

    assert docker_info.container_id == "abc123"
    assert docker_info.container_name == "test_container"
    assert docker_info.docker_status == "running"  # default
    assert docker_info.vllm_status == "starting"  # default


def test_gpu_info_creation():
    """Test GPUInfo creation."""
    gpu = GPUInfo(index="0", name="Tesla T4", memory_used=8000, memory_total=16000, utilization=75)

    assert gpu.index == 0  # Converted to int
    assert gpu.name == "Tesla T4"
    assert gpu.memory_used == 8000
    assert gpu.memory_total == 16000
    assert gpu.utilization == 75


def test_gpu_info_dataclass_to_dict():
    """Test converting dataclasses to dict for JSON serialization."""
    env = EnvInfo(base_url="http://localhost:8000/v1/", port=8000, devices="0")

    env_dict = asdict(env)

    assert env_dict["base_url"] == "http://localhost:8000/v1/"
    assert env_dict["port"] == 8000
    assert env_dict["devices"] == "0"

    # Should be JSON serializable
    json_str = json.dumps(env_dict)
    assert json_str is not None


def test_model_info_has_uuid():
    """Test that ModelInfo generates a unique ID."""
    model1 = ModelInfo(
        model_name="test-model",
        model_name_short="test",
        gpu_memory_utilization=0.9,
        max_model_len=4096,
    )
    model2 = ModelInfo(
        model_name="test-model",
        model_name_short="test",
        gpu_memory_utilization=0.9,
        max_model_len=4096,
    )

    # Each instance should have a unique ID
    assert model1.id != model2.id
    assert len(model1.id) == 36  # UUID format


def test_docker_info_vllm_status():
    """Test VLLM status tracking in DockerInfo."""
    docker_info = DockerInfo(
        container_id="abc123",
        container_name="test_container",
        image_name="vllm/vllm-openai",
        image_tag="v0.9.1",
        docker_port="8000/tcp",
        devices="0",
        vllm_status="running",
    )

    assert docker_info.vllm_status == "running"

    # Test default value
    docker_info_default = DockerInfo(
        container_id="def456",
        container_name="test_container2",
        image_name="vllm/vllm-openai",
        image_tag="v0.9.1",
        docker_port="8000/tcp",
        devices="0",
    )
    assert docker_info_default.vllm_status == "starting"
