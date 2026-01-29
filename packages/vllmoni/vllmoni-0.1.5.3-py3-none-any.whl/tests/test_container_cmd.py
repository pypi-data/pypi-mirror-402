"""Unit tests for container command generation."""

from vllmoni.app.models import EnvInfo, ModelInfo, UserInfo
from vllmoni.container.cmd import (
    add_disable_log_requests,
    add_disable_log_stats,
    add_dtype,
    add_enforce_eager,
    add_env_var,
    add_gpus,
    add_max_model_len,
    add_model_flags,
    add_name,
    add_port,
    add_tensor_parallel_size,
    add_tokenizer,
    add_tool_support,
    add_trust_remote_code,
    create_docker_command,
    docker_run_base,
)


def test_docker_run_base():
    """Test base docker run command."""
    cmd = docker_run_base()
    assert cmd == ["docker", "run", "-d"]


def test_add_env_var():
    """Test adding environment variable."""
    result = add_env_var("TEST_VAR", "test_value")
    assert result == ["--env", "TEST_VAR=test_value"]


def test_add_gpus_with_devices():
    """Test adding GPU devices."""
    cmd = []
    result = add_gpus(cmd, "0,1")
    assert "--gpus" in result
    assert "device=0,1" in result


def test_add_gpus_all():
    """Test adding all GPUs."""
    cmd = []
    result = add_gpus(cmd, None)
    assert "--gpus" in result
    assert "all" in result


def test_add_name():
    """Test generating container name."""
    result = add_name("testuser", "llama3", 42)
    assert len(result) == 2
    assert result[0] == "--name"
    assert result[1] == "vllmoni_testuser_llama3_42"


def test_add_name_with_special_characters():
    """Test container name sanitization with special characters."""
    result = add_name("test@user#123", "model/name:v1", 99)
    assert len(result) == 2
    assert result[0] == "--name"
    # Special characters should be replaced with underscores
    assert result[1] == "vllmoni_test_user_123_model_name_v1_99"


def test_add_name_without_seed():
    """Test container name generation without seed."""
    result = add_name("testuser", "llama3", None)
    assert len(result) == 2
    assert result[0] == "--name"
    # Should have random number
    assert result[1].startswith("vllmoni_testuser_llama3_")


def test_add_port():
    """Test adding port mapping."""
    result = add_port(8080)
    assert result == ["-p", "8080:8000"]


def test_add_model_flags():
    """Test adding model flags."""
    result = add_model_flags(
        ModelInfo(
            model_name="meta-llama/Llama-3-8B",
            model_name_short="llama3",
            gpu_memory_utilization=0.9,
            max_model_len=4096,
        ),
        "test_api_key",
    )
    assert "--model" in result
    assert "meta-llama/Llama-3-8B" in result
    assert "--api-key" in result
    assert "test_api_key" in result


def test_add_dtype_auto():
    """Test adding dtype with auto."""
    result = add_dtype([], None)
    assert "--dtype" in result
    assert "auto" in result


def test_add_dtype_custom():
    """Test adding custom dtype."""
    result = add_dtype([], "float16")
    assert "--dtype" in result
    assert "float16" in result


def test_add_enforce_eager_enabled():
    """Test adding enforce eager flag when enabled."""
    result = add_enforce_eager([], True)
    assert "--enforce-eager" in result


def test_add_enforce_eager_disabled():
    """Test not adding enforce eager flag when disabled."""
    result = add_enforce_eager([], False)
    assert "--enforce-eager" not in result


def test_add_tool_support_with_parser():
    """Test adding tool support with parser."""
    model = ModelInfo(
        model_name="test-model",
        model_name_short="test",
        gpu_memory_utilization=0.9,
        max_model_len=4096,
        tool_call_parser="mistral",
    )
    result = add_tool_support([], model)
    assert "--enable-auto-tool-choice" in result
    assert "--tool-call-parser" in result
    assert "mistral" in result


def test_add_tool_support_without_parser():
    """Test not adding tool support without parser."""
    model = ModelInfo(
        model_name="test-model",
        model_name_short="test",
        gpu_memory_utilization=0.9,
        max_model_len=4096,
    )
    result = add_tool_support([], model)
    assert "--enable-auto-tool-choice" not in result


def test_add_tokenizer():
    """Test adding custom tokenizer."""
    result = add_tokenizer([], "custom-tokenizer")
    assert "--tokenizer" in result
    assert "custom-tokenizer" in result


def test_add_max_model_len():
    """Test adding max model length."""
    result = add_max_model_len([], 8192)
    assert "--max-model-len" in result
    assert "8192" in result


def test_add_tensor_parallel_size():
    """Test adding tensor parallel size."""
    result = add_tensor_parallel_size([], 2)
    assert "--tensor-parallel-size" in result
    assert "2" in result


def test_add_trust_remote_code_enabled():
    """Test enabling trust remote code."""
    result = add_trust_remote_code([], True)
    assert "--trust-remote-code" in result


def test_add_trust_remote_code_disabled():
    """Test not enabling trust remote code."""
    result = add_trust_remote_code([], False)
    assert "--trust-remote-code" not in result


def test_add_disable_log_requests():
    """Test disabling log requests."""
    result = add_disable_log_requests([], True)
    assert "--disable-log-requests" in result


def test_add_disable_log_stats():
    """Test disabling log stats."""
    result = add_disable_log_stats([], True)
    assert "--disable-log-stats" in result


def test_create_docker_command_basic():
    """Test creating a complete docker command."""
    model_info = ModelInfo(
        model_name="meta-llama/Llama-3-8B",
        model_name_short="llama3",
        gpu_memory_utilization=0.9,
        max_model_len=4096,
        seed=42,
    )
    env_info = EnvInfo(base_url="http://localhost:8000/v1/", port=8000, devices="0")
    user_info = UserInfo(user_name="testuser", user_id="1000", group_id="1000")
    env_vars = {
        "HUGGING_FACE_HUB_TOKEN": "test_token",
        "HF_HOME": "/tmp/hf",
        "VLLM_API_KEY": "test_key",
    }

    cmd = create_docker_command(model_info, env_info, env_vars, user_info)

    # Check essential components
    assert "docker" in cmd
    assert "run" in cmd
    assert "-d" in cmd
    assert "--name" in cmd
    assert "--runtime" in cmd
    assert "nvidia" in cmd
    assert "--gpus" in cmd
    assert "-p" in cmd
    assert "8000:8000" in cmd
    assert "--model" in cmd
    assert "meta-llama/Llama-3-8B" in cmd
    assert "--api-key" in cmd
    assert "--gpu-memory-utilization" in cmd
    assert "0.9" in cmd
    assert "--max-model-len" in cmd
    assert "4096" in cmd
    assert "--seed" in cmd
    assert "42" in cmd


def test_create_docker_command_with_optional_features():
    """Test creating docker command with optional features."""
    model_info = ModelInfo(
        model_name="test-model",
        model_name_short="test",
        gpu_memory_utilization=0.8,
        max_model_len=2048,
        enforce_eager=True,
        trust_remote_code=True,
        tool_call_parser="mistral",
        tokenizer="custom-tokenizer",
        tensor_parallel_size=2,
        disable_log_requests=True,
        seed=100,
    )
    env_info = EnvInfo(base_url="http://localhost:8001/v1/", port=8001, devices="0,1")
    user_info = UserInfo(user_name="testuser", user_id="1000", group_id="1000")
    env_vars = {
        "HUGGING_FACE_HUB_TOKEN": "token",
        "HF_HOME": "/tmp/hf",
        "VLLM_API_KEY": "key",
    }

    cmd = create_docker_command(model_info, env_info, env_vars, user_info)

    # Check optional features
    assert "--enforce-eager" in cmd
    assert "--trust-remote-code" in cmd
    assert "--tool-call-parser" in cmd
    assert "mistral" in cmd
    assert "--tokenizer" in cmd
    assert "custom-tokenizer" in cmd
    assert "--tensor-parallel-size" in cmd
    assert "2" in cmd
    assert "--disable-log-requests" in cmd
