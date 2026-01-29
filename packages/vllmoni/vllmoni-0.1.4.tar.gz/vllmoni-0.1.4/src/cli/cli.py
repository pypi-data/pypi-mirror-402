import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import docker
import requests
import typer
import yaml
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from rich import box
from rich.console import Console
from rich.table import Table
from sqlalchemy.orm import Session

from app.db import get_session, init_db
from app.models import EnvInfo, GPUInfo, ModelInfo, TableRow, UserInfo
from app.repository import ModelRepository
from container import run_container, stop_container
from utils.logger import logger

app = typer.Typer(name="vllmoni", help="Monitor and manage running VLLM models")


def my_compose(overrides: Optional[list[str]]) -> DictConfig:
    # Support loading configs from user directory
    user_config_dir = Path.home() / ".vllmoni" / "conf"

    # Use environment variable to specify additional config paths
    user_config_env = os.environ.get("VLLMONI_CONFIG_PATH", "")
    if user_config_env:
        user_config_dir = Path(user_config_env)

    # Try to find if user specified a custom model that doesn't exist in defaults
    model_override = None
    if overrides:
        for override in overrides:
            if override.startswith("model="):
                model_override = override.split("=")[1]
                break

    # Check if the model override refers to a user config file
    use_user_config = False
    user_model_config_path = None
    if model_override and user_config_dir.exists():
        user_model_config_path = user_config_dir / "model" / f"{model_override}.yaml"
        if user_model_config_path.exists():
            use_user_config = True
            # Remove model override from overrides list, we'll load default first
            overrides = [o for o in overrides if not o.startswith("model=")]

    # Initialize with default config path (must be relative)
    with initialize(config_path="../../conf", job_name="vllmoni", version_base=None):
        # Load config with overrides (without model override if using user config)
        cfg = compose(config_name="defaults", overrides=overrides)

        # If user specified a custom model config, load and merge it
        if use_user_config and user_model_config_path:
            try:
                with open(user_model_config_path, "r") as f:
                    user_model_data = yaml.safe_load(f)
                    if user_model_data is not None:
                        # Temporarily disable struct mode to allow adding new keys
                        OmegaConf.set_struct(cfg.model, False)
                        # Replace model config with user config
                        for key, value in user_model_data.items():
                            cfg.model[key] = value
                        # Re-enable struct mode
                        OmegaConf.set_struct(cfg.model, True)
                        logger.info(f"Loaded user model config from: {user_model_config_path}")
            except (IOError, yaml.YAMLError) as e:
                logger.error(f"Failed to load user model config from {user_model_config_path}: {e}")
                logger.warning("Falling back to default model configuration")

        return cfg


@app.command()
def init(
    override: bool = typer.Option(False, "--override", help="Override existing DB"),
):
    init_db(override)


@app.command()
def ls(
    full: bool = typer.Option(False, "--full", help="Show full table info"),
    interval: Optional[float] = typer.Option(None, "-i", "--interval", help="Refresh interval (seconds)"),
):
    """List all registered models."""
    console = Console()

    def render():
        session: Session = get_session()
        repo = ModelRepository(session)
        rows = repo.get_all()

        if not rows:
            logger.info("No entries found.")
            return

        table = Table(title="", box=box.MARKDOWN)
        table.add_column("ID", style="blue")
        table.add_column("Model", style="green")
        table.add_column("URL", style="green")
        table.add_column("User", style="magenta")
        table.add_column("User Info", style="magenta")
        table.add_column("Memory", style="yellow")
        table.add_column("Usage", style="yellow")
        table.add_column("VLLM Status", style="cyan")
        table.add_column("Docker ID", style="blue")
        table.add_column("Docker Image", style="blue")
        table.add_column("Created", justify="right", style="blue")

        for row in rows:
            env = json.loads(row.env_info)
            model = json.loads(row.model_info)
            user = json.loads(row.user_info)
            docker = json.loads(row.docker_info or "{}")
            gpu_infos = json.loads(row.gpu_infos or "[]")
            gpu_info_objs = [GPUInfo(**info) if isinstance(info, dict) else info for info in gpu_infos]

            base_cols = [
                str(row.id),
                model.get("model_name_short", ""),
                env.get("base_url", ""),
                user.get("user_name", ""),
                f"{user.get('user_id', '')}:{user.get('group_id', '')}",
                f"{sum(info.memory_used for info in gpu_info_objs)}/{sum(info.memory_total for info in gpu_info_objs)} MB",  # noqa: E501
                f"{sum(info.utilization for info in gpu_info_objs) / len(gpu_info_objs) if gpu_info_objs else 0:.2f} %",
                docker.get("vllm_status", "unknown"),
                docker.get("container_id", ""),
                f"{docker.get('image_name', '')}:{docker.get('image_tag', '')}",
                str(row.created),
            ]

            table.add_row(*base_cols)

        console.print(table)

    if interval is not None:
        try:
            while True:
                os.system("clear" if os.name == "posix" else "cls")
                render()
                time.sleep(interval)
        except KeyboardInterrupt:
            pass
    else:
        render()


@app.command()
def monitor_container(container_id: str, model_id: int) -> None:
    client: docker.DockerClient = docker.from_env()
    log_path = Path(f"logs/monitor_{model_id}.log")

    def write_log(msg: str):
        with log_path.open("a") as f:
            f.write(msg + "\n")

    logger.info(f"Monitoring container: {container_id}")
    write_log(f"Monitoring container: {container_id}")

    # Check VLLM health and update status
    session: Session = get_session()
    repo = ModelRepository(session)
    row = repo.get(model_id)

    if row:
        env = json.loads(row.env_info)
        base_url = env.get("base_url", "").rstrip("/")

        # Try to detect when VLLM is ready by checking the health endpoint
        max_attempts = 60  # Wait up to 60 seconds
        health_check_passed = False
        for _ in range(max_attempts):
            try:
                response = requests.get(f"{base_url}/models", timeout=2)
                if response.status_code == 200:
                    repo.update_vllm_status(model_id, "running")
                    msg = f"✅ VLLM server is ready: {base_url}"
                    logger.info(msg)
                    write_log(msg)
                    health_check_passed = True
                    break
            except requests.RequestException:
                pass
            time.sleep(1)

        # If health check never passed, mark as timeout
        if not health_check_passed:
            try:
                repo.update_vllm_status(model_id, "timeout")
                msg = f"⏱️ VLLM server health check timed out after {max_attempts} seconds"
                logger.warning(msg)
                write_log(msg)
            except Exception as e:
                logger.error(f"Failed to update timeout status: {e}")

    for event in client.events(decode=True):
        if (
            event.get("Type") == "container"
            and event.get("Action") in ["die", "stop"]
            and event.get("id", "").startswith(container_id)
        ):
            msg = f"🛑 Container stopped unexpectedly: {container_id}"
            logger.info(msg)
            write_log(msg)
            stop(model_id)
            break


@app.command()
def monitor_gpu(devices: str, model_id: int):
    """Monitor GPU usage and write updates to DB every second."""
    gpu_indices = [int(d.strip()) for d in devices.split(",")]
    log_path = Path(f"logs/gpu_monitor_{model_id}.log")
    session: Session = get_session()
    repo = ModelRepository(session)

    def write_log(msg: str):
        with log_path.open("a") as f:
            f.write(f"{datetime.now(timezone.utc)} - {msg}\n")

    write_log(f"Started monitoring GPUs: {gpu_indices}")
    logger.info(f"Started monitoring GPUs: {gpu_indices}")

    while True:
        gpu_data = []
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.used,memory.total,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in result.stdout.strip().split("\n"):
                parts = line.split(", ")
                if len(parts) == 5 and int(parts[0]) in gpu_indices:
                    info = GPUInfo(index=parts[0])
                    gpu_data.append(info)
                    write_log(
                        f"GPU {info.index}: {info.name} | {info.memory_used}/{info.memory_total} MB | Util: {info.utilization}%"  # noqa: E501
                    )
            # DB insert here (assumes a helper function)
            repo.update_gpu_infos(model_id=model_id, gpu_infos=gpu_data)

        except subprocess.CalledProcessError as e:
            write_log(f"Error fetching GPU info: {e}")
            logger.error(f"GPU monitor error: {e}")

        time.sleep(1)


@app.command()
def run(
    overrides: Optional[list[str]] = typer.Argument(None),
    follow: bool = typer.Option(False, "-f", "--follow", help="Follow log output (live logs)"),
):
    logger.info(f"Using devices: {os.environ['CUDA_VISIBLE_DEVICES']}")

    # Load Database
    session: Session = get_session()
    repo = ModelRepository(session)

    # Load Hydra configuration
    cfg = my_compose(overrides)
    os.environ["CUDA_VISIBLE_DEVICES"] = str(cfg.devices) if cfg.devices else "0"
    env_info = EnvInfo(cfg.base_url, cfg.port, cfg.devices, cfg.image_name, cfg.image_tag)
    logger.info(f"Using environment: {env_info}")

    # Init the model
    model_info = ModelInfo(**cfg.model)  # type: ignore
    logger.info(model_info)

    # User Infos
    user_info = UserInfo.from_current_user()
    logger.info(user_info)

    # GPU Infos
    for device in str(cfg.devices).split(","):
        gpu_info = GPUInfo(device.strip())
        logger.info(gpu_info)

    try:
        docker_info = run_container(model_info, env_info, user_info)
    except ValueError as e:
        # Print error to stdout and exit with non-zero code
        print(str(e))
        raise typer.Exit(code=1) from e

    if not docker_info:
        logger.error("Failed to run container.")
        raise typer.Exit(code=1)

    try:
        table_row = TableRow(
            env_info=json.dumps(asdict(env_info)),
            model_info=json.dumps(asdict(model_info)),
            user_info=json.dumps(asdict(user_info)),
            docker_info=json.dumps(asdict(docker_info)) if docker_info is not None else json.dumps({}),
            gpu_infos=json.dumps([asdict(GPUInfo(device.strip())) for device in str(cfg.devices).split(",")]),
        )
        result = repo.create(table_row)
        logger.info(f"Model registered: {result.id}")

        # Subprozess für Monitoring starten
        if docker_info and docker_info.container_id:
            log_path = Path(f"logs/monitor_{result.id}.log")
            subprocess.Popen(
                [
                    sys.executable,
                    __file__,
                    "monitor-container",
                    docker_info.container_id,
                    str(result.id),
                ],
                stdout=log_path.open("a"),
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            logger.info(f"Monitoring started in background: {log_path}")

            # Monitor GPU usage
            subprocess.Popen(
                [
                    sys.executable,
                    __file__,
                    "monitor-gpu",
                    str(cfg.devices),
                    str(result.id),
                ],
                stdout=log_path.open("a"),
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

            # Print logs if requested
            if follow:
                client = docker.from_env()
                console = Console()
                try:
                    container = client.containers.get(docker_info.container_id)
                    for line in container.logs(stream=True, follow=True):
                        console.print(line.decode("utf-8").rstrip())
                except Exception as e:
                    logger.error(f"Error fetching logs for container {docker_info.container_id}: {e}")

    except Exception as e:
        logger.error(f"Error during registration: {e}")


@app.command()
def stop(vllmoni_id: int) -> None:
    logger.info(f"Stopping ID: {vllmoni_id}")
    session: Session = get_session()
    repo = ModelRepository(session)
    row = repo.get(vllmoni_id)
    if not row:
        logger.error(f"No model with ID: {vllmoni_id}")
        return
    docker_info = json.loads(row.docker_info or "{}")
    container_id = docker_info.get("container_id")
    if not container_id:
        logger.info(f"No container for {vllmoni_id}")
        # Don't proceed if no container
        result = repo.delete(vllmoni_id)
        if result.get("error"):
            logger.error(f"Deregister error: {result['error']}")
        else:
            logger.info(f"{vllmoni_id} deregistered")
        return

    # Update status to stopping
    try:
        repo.update_vllm_status(vllmoni_id, "stopping")
        logger.info(f"VLLM status set to 'stopping' for {vllmoni_id}")
    except Exception as e:
        logger.warning(f"Could not update status: {e}")

    try:
        stop_container(container_id)
    except Exception as e:
        logger.error(f"Stop error: {e}")
    result = repo.delete(vllmoni_id)
    if result.get("error"):
        logger.error(f"Deregister error: {result['error']}")
    else:
        logger.info(f"{vllmoni_id} deregistered")


@app.command()
def stop_all() -> None:
    logger.info("Stopping all models.")

    session: Session = get_session()
    repo = ModelRepository(session)
    rows = repo.get_all()

    # Stop all running containers
    for row in rows:
        docker_info = json.loads(row.docker_info or "{}")
        container_id = docker_info.get("container_id")
        if container_id:
            # Update status to stopping
            try:
                repo.update_vllm_status(row.id, "stopping")
                logger.info(f"VLLM status set to 'stopping' for {row.id}")
            except Exception as e:
                logger.warning(f"Could not update status for {row.id}: {e}")

            try:
                stop_container(container_id)
                logger.info(f"Stopped container: {container_id}")
            except Exception as e:
                logger.error(f"Error stopping container {container_id}: {e}")

    # Delete all model records
    result = repo.delete_all()
    if result.get("error"):
        logger.error(f"Failed to deregister: {result['error']}")
    else:
        logger.info("All models deregistered.")


@app.command()
def logs(
    vllmoni_id: int,
    tail: int = typer.Option(100, "--tail", help="Number of lines to show from the end of the log file"),
    follow: bool = typer.Option(False, "-f", "--follow", help="Follow log output (live logs)"),
):
    """Show logs for a specific model."""
    session: Session = get_session()
    repo = ModelRepository(session)
    row = repo.get(vllmoni_id)
    if not row:
        logger.error(f"No model with ID: {vllmoni_id}")
        return

    docker_info = json.loads(row.docker_info or "{}")
    container_id = docker_info.get("container_id", "")
    if not container_id:
        logger.error(f"No container found for model ID: {vllmoni_id}")
        return

    client = docker.from_env()
    console = Console()
    try:
        container = client.containers.get(container_id)
        if follow:
            for line in container.logs(stream=True, tail=tail, follow=True):
                console.print(line.decode("utf-8").rstrip())
        else:
            logs = container.logs(tail=tail).decode("utf-8")
            console.print(logs.rstrip())
    except Exception as e:
        logger.error(f"Error fetching logs for container {container_id}: {e}")


if __name__ == "__main__":
    app()
