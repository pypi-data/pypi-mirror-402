"""Unit tests for ModelRepository."""

import json
from dataclasses import asdict

from app.models import (
    EnvInfo,
    GPUInfo,
    ModelInfo,
    TableRow,
    UserInfo,
)
from app.repository import ModelRepository


def test_repository_create(temp_db):
    """Test creating a new model entry in the repository."""
    repo = ModelRepository(temp_db)

    # Create test data
    env_info = EnvInfo(base_url="http://localhost:8000/v1/", port=8000, devices="0")
    model_info = ModelInfo(
        model_name="test-model",
        model_name_short="test",
        gpu_memory_utilization=0.9,
        max_model_len=4096,
    )
    user_info = UserInfo(user_name="testuser", user_id="1000", group_id="1000")

    table_row = TableRow(
        env_info=json.dumps(asdict(env_info)),
        model_info=json.dumps(asdict(model_info)),
        user_info=json.dumps(asdict(user_info)),
        docker_info=json.dumps({}),
        gpu_infos=json.dumps([]),
    )

    # Create entry
    result = repo.create(table_row)

    # Verify
    assert result.id is not None
    assert result.created is not None
    assert json.loads(result.env_info)["port"] == 8000
    assert json.loads(result.model_info)["model_name"] == "test-model"


def test_repository_get_all(temp_db):
    """Test getting all model entries from the repository."""
    repo = ModelRepository(temp_db)

    # Initially empty
    assert len(repo.get_all()) == 0

    # Add some entries
    for i in range(3):
        table_row = TableRow(
            env_info=json.dumps({"port": 8000 + i}),
            model_info=json.dumps({"model_name": f"model-{i}"}),
            user_info=json.dumps({"user_name": "testuser"}),
            docker_info=json.dumps({}),
            gpu_infos=json.dumps([]),
        )
        repo.create(table_row)

    # Should have 3 entries
    all_rows = repo.get_all()
    assert len(all_rows) == 3


def test_repository_get(temp_db):
    """Test getting a specific model by ID."""
    repo = ModelRepository(temp_db)

    # Create entry
    table_row = TableRow(
        env_info=json.dumps({"port": 8000}),
        model_info=json.dumps({"model_name": "test-model"}),
        user_info=json.dumps({"user_name": "testuser"}),
        docker_info=json.dumps({}),
        gpu_infos=json.dumps([]),
    )
    created = repo.create(table_row)

    # Get by ID
    retrieved = repo.get(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id
    assert json.loads(retrieved.model_info)["model_name"] == "test-model"


def test_repository_get_nonexistent(temp_db):
    """Test getting a nonexistent model returns None."""
    repo = ModelRepository(temp_db)

    result = repo.get(999)
    assert result is None


def test_repository_update(temp_db):
    """Test updating a model entry."""
    repo = ModelRepository(temp_db)

    # Create entry
    table_row = TableRow(
        env_info=json.dumps({"port": 8000}),
        model_info=json.dumps({"model_name": "test-model"}),
        user_info=json.dumps({"user_name": "testuser"}),
        docker_info=json.dumps({}),
        gpu_infos=json.dumps([]),
    )
    created = repo.create(table_row)

    # Update
    new_docker_info = json.dumps({"container_id": "abc123"})
    repo.update(created.id, docker_info=new_docker_info)

    # Verify update
    updated = repo.get(created.id)
    assert json.loads(updated.docker_info)["container_id"] == "abc123"


def test_repository_update_gpu_infos(temp_db):
    """Test updating GPU information for a model."""
    repo = ModelRepository(temp_db)

    # Create entry
    table_row = TableRow(
        env_info=json.dumps({"port": 8000}),
        model_info=json.dumps({"model_name": "test-model"}),
        user_info=json.dumps({"user_name": "testuser"}),
        docker_info=json.dumps({}),
        gpu_infos=json.dumps([]),
    )
    created = repo.create(table_row)

    # Update GPU info
    gpu_infos = [
        GPUInfo(
            index="0",
            name="Tesla T4",
            memory_used=1000,
            memory_total=16000,
            utilization=50,
        )
    ]
    repo.update_gpu_infos(created.id, gpu_infos)

    # Verify update
    updated = repo.get(created.id)
    gpu_data = json.loads(updated.gpu_infos)
    assert len(gpu_data) == 1
    assert gpu_data[0]["name"] == "Tesla T4"
    assert gpu_data[0]["memory_used"] == 1000


def test_repository_delete(temp_db):
    """Test deleting a model entry."""
    repo = ModelRepository(temp_db)

    # Create entry
    table_row = TableRow(
        env_info=json.dumps({"port": 8000}),
        model_info=json.dumps({"model_name": "test-model"}),
        user_info=json.dumps({"user_name": "testuser"}),
        docker_info=json.dumps({}),
        gpu_infos=json.dumps([]),
    )
    created = repo.create(table_row)

    # Delete
    result = repo.delete(created.id)
    assert result["status"] == "deleted"
    assert result["container_id"] == created.id

    # Verify deletion
    assert repo.get(created.id) is None


def test_repository_delete_nonexistent(temp_db):
    """Test deleting a nonexistent model returns error."""
    repo = ModelRepository(temp_db)

    result = repo.delete(999)
    assert "error" in result
    assert result["code"] == 404


def test_repository_delete_all(temp_db):
    """Test deleting all model entries."""
    repo = ModelRepository(temp_db)

    # Add multiple entries
    for i in range(3):
        table_row = TableRow(
            env_info=json.dumps({"port": 8000 + i}),
            model_info=json.dumps({"model_name": f"model-{i}"}),
            user_info=json.dumps({"user_name": "testuser"}),
            docker_info=json.dumps({}),
            gpu_infos=json.dumps([]),
        )
        repo.create(table_row)

    assert len(repo.get_all()) == 3

    # Delete all
    result = repo.delete_all()
    assert result["status"] == "all deleted"

    # Verify all deleted
    assert len(repo.get_all()) == 0


def test_repository_update_vllm_status(temp_db):
    """Test updating VLLM status for a model."""
    repo = ModelRepository(temp_db)

    # Create entry with docker_info
    table_row = TableRow(
        env_info=json.dumps({"port": 8000}),
        model_info=json.dumps({"model_name": "test-model"}),
        user_info=json.dumps({"user_name": "testuser"}),
        docker_info=json.dumps({"container_id": "abc123", "vllm_status": "starting"}),
        gpu_infos=json.dumps([]),
    )
    created = repo.create(table_row)

    # Update VLLM status to running
    repo.update_vllm_status(created.id, "running")

    # Verify update
    updated = repo.get(created.id)
    docker_info = json.loads(updated.docker_info)
    assert docker_info["vllm_status"] == "running"
    assert docker_info["container_id"] == "abc123"  # Other fields preserved

    # Update to stopping
    repo.update_vllm_status(created.id, "stopping")
    updated = repo.get(created.id)
    docker_info = json.loads(updated.docker_info)
    assert docker_info["vllm_status"] == "stopping"


def test_repository_update_vllm_status_validation(temp_db):
    """Test that update_vllm_status validates status values."""
    repo = ModelRepository(temp_db)
    import pytest

    # Create entry
    table_row = TableRow(
        env_info=json.dumps({"port": 8000}),
        model_info=json.dumps({"model_name": "test-model"}),
        user_info=json.dumps({"user_name": "testuser"}),
        docker_info=json.dumps({"container_id": "abc123", "vllm_status": "starting"}),
        gpu_infos=json.dumps([]),
    )
    created = repo.create(table_row)

    # Test invalid status value
    with pytest.raises(ValueError) as excinfo:
        repo.update_vllm_status(created.id, "invalid_status")
    assert "Invalid vllm_status" in str(excinfo.value)
