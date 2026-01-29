"""Main script for starting the VLLM server."""

import json
import os
import subprocess
from typing import Optional

from dotenv import load_dotenv

from vllmoni.app.models import DockerInfo, EnvInfo, ModelInfo, UserInfo
from vllmoni.container.cmd import create_docker_command
from vllmoni.utils.logger import logger

load_dotenv()


def run(model: ModelInfo, env_info: EnvInfo, user_info: UserInfo) -> Optional[DockerInfo]:
    """Main function for starting the VLLM server."""
    # Load environment variables from .env file

    env_vars = {
        "HUGGING_FACE_HUB_TOKEN": os.getenv("HUGGING_FACE_HUB_TOKEN"),
        "HF_HOME": os.getenv("HUGGINGFACE_CACHE_DIR", os.path.expanduser("~/.cache/huggingface")),
        "VLLM_API_KEY": os.getenv("VLLM_API_KEY"),
    }

    if not env_vars["VLLM_API_KEY"]:
        raise ValueError("VLLM_API_KEY key is not set. Please set VLLM_API_KEY in the environment.")
    # Ensure the Hugging Face cache directory exists
    os.makedirs(env_vars["HF_HOME"], exist_ok=True)

    # Create the Docker command
    docker_command = create_docker_command(model, env_info, env_vars, user_info)

    # Execute the Docker command
    try:
        logger.info(f"Running Docker command: {' '.join(docker_command)}")
        result = subprocess.run(docker_command, capture_output=True, text=True, check=True)
        container_id = result.stdout.strip()

        # Fetch
        inspect_result = subprocess.run(
            ["docker", "inspect", container_id],
            capture_output=True,
            text=True,
            check=True,
        )
        inspect_data = json.loads(inspect_result.stdout)[0]

        return DockerInfo.from_inspect_data(inspect_data, env_info.devices)

    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.stderr}")
        return None
