import subprocess

from utils.logger import logger


def stop(container_id: str) -> bool:
    """Stop and remove a Docker container by its ID."""
    try:
        subprocess.run(["docker", "stop", container_id], check=True)
        logger.info(f"[docker] Container {container_id} stopped.")

        subprocess.run(["docker", "rm", container_id], check=True)
        logger.info(f"[docker] Container {container_id} removed.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"[docker] Error stopping/removing {container_id}: {e}")
        return False
