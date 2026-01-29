"""Test user config loading from ~/.vllmoni/conf/model/"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from vllmoni.cli.cli import my_compose


def test_user_config_loading():
    """Test that user configs are loaded from ~/.vllmoni/conf/model/"""
    # Create a temporary user config directory
    with tempfile.TemporaryDirectory() as tmpdir:
        user_config_dir = Path(tmpdir) / ".vllmoni" / "conf" / "model"
        user_config_dir.mkdir(parents=True)

        # Create a test model config
        test_config = {
            "model_name": "test/custom-model",
            "model_name_short": "custom-test",
            "gpu_memory_utilization": 0.8,
            "temperature": 0.9,
            "max_tokens": 3000,
            "max_model_len": 10000,
            "tensor_parallel_size": 2,
        }

        test_config_file = user_config_dir / "custom_test.yaml"
        with open(test_config_file, "w") as f:
            yaml.dump(test_config, f)

        # Mock Path.home() to return our temp directory
        with patch("pathlib.Path.home", return_value=Path(tmpdir)):
            # Load config with model override pointing to our custom config
            cfg = my_compose(overrides=["model=custom_test"])

            # Verify that the custom config values were loaded
            assert cfg.model.model_name == "test/custom-model"
            assert cfg.model.model_name_short == "custom-test"
            assert cfg.model.gpu_memory_utilization == 0.8
            assert cfg.model.temperature == 0.9
            assert cfg.model.max_tokens == 3000


def test_env_var_config_path():
    """Test that VLLMONI_CONFIG_PATH environment variable is respected"""
    with tempfile.TemporaryDirectory() as tmpdir:
        custom_config_dir = Path(tmpdir) / "custom_conf" / "model"
        custom_config_dir.mkdir(parents=True)

        # Create a test model config in custom location
        test_config = {
            "model_name": "env/test-model",
            "model_name_short": "env-test",
            "gpu_memory_utilization": 0.6,
            "temperature": 0.5,
            "max_tokens": 1500,
            "max_model_len": 5000,
            "tensor_parallel_size": 1,
        }

        test_config_file = custom_config_dir / "env_test.yaml"
        with open(test_config_file, "w") as f:
            yaml.dump(test_config, f)

        # Set environment variable
        with patch.dict(os.environ, {"VLLMONI_CONFIG_PATH": str(custom_config_dir.parent)}):
            # Load config with model override
            cfg = my_compose(overrides=["model=env_test"])

            # Verify that the custom config values were loaded
            assert cfg.model.model_name == "env/test-model"
            assert cfg.model.model_name_short == "env-test"
            assert cfg.model.gpu_memory_utilization == 0.6


def test_default_config_fallback():
    """Test that default configs work when no user config exists"""
    with tempfile.TemporaryDirectory() as tmpdir, patch("pathlib.Path.home", return_value=Path(tmpdir)):
        # Load a default config (xlam-8b is the default in conf/defaults.yaml)
        cfg = my_compose(overrides=[])

        # Should load default model config successfully
        assert cfg.model is not None
        assert "model_name" in cfg.model


def test_malformed_user_config_fallback():
    """Test that malformed user configs fall back to default gracefully"""
    with tempfile.TemporaryDirectory() as tmpdir:
        user_config_dir = Path(tmpdir) / ".vllmoni" / "conf" / "model"
        user_config_dir.mkdir(parents=True)

        # Create a malformed YAML file
        test_config_file = user_config_dir / "malformed_test.yaml"
        with open(test_config_file, "w") as f:
            f.write("{ invalid: yaml: content: [")

        # Mock Path.home() to return our temp directory
        with patch("pathlib.Path.home", return_value=Path(tmpdir)):
            # Load config with model override pointing to malformed config
            # Should fall back to default without raising an exception
            cfg = my_compose(overrides=["model=malformed_test"])

            # Should have loaded default model config
            assert cfg.model is not None
            assert "model_name" in cfg.model
