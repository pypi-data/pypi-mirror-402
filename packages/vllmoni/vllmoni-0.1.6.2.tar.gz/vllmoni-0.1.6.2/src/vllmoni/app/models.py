# app/registry.py
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Literal, Optional

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


@dataclass
class EnvInfo:
    """Environment Information dataclass."""

    base_url: str
    port: int
    devices: Optional[str] = None
    image_name: Literal["vllm/vllm-openai"] = "vllm/vllm-openai"
    image_tag: str = "v0.9.1"


@dataclass
class ModelInfo:
    """Configuration dataclass for the hydra modules."""

    model_name: str
    model_name_short: str
    gpu_memory_utilization: float
    max_model_len: int
    top_p: float = 0.95
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tensor_parallel_size: int = 1
    dtype: Optional[str] = None

    # Additional VLLM parameters (optional)
    enforce_eager: bool = False
    quantization: Optional[str] = None
    tool_call_parser: Optional[str] = None
    tokenizer: Optional[str] = None
    trust_remote_code: bool = False
    disable_log_requests: bool = False
    disable_log_stats: bool = False
    max_concurrent_requests: Optional[int] = None
    max_log_len: Optional[int] = None
    seed: Optional[int] = None
    max_num_seqs: Optional[int] = None
    disable_deployment_check: bool = False
    no_enable_prefix_caching: bool = False


@dataclass
class UserInfo:
    """User Information dataclass."""

    user_name: str
    user_id: str
    user_role: str = ""
    group_id: str = ""

    @classmethod
    def from_current_user(cls) -> "UserInfo":
        uid = os.getuid()
        gid = os.getgid()
        user_name = os.getlogin()

        return cls(
            user_name=user_name,
            user_id=str(uid),
            group_id=str(gid),
        )


@dataclass
class DockerInfo:
    """Docker Information dataclass."""

    container_id: str
    container_name: str
    image_name: str
    image_tag: str
    docker_port: str
    docker_status: str = "running"
    vllm_status: str = "starting"
    docker_version: str = ""
    env: List[str] = field(default_factory=list)
    devices: Optional[str] = None

    @classmethod
    def from_inspect_data(cls, inspect_data: dict, devices: Optional[str]) -> "DockerInfo":
        container_id = inspect_data.get("Id", "")[:12]
        container_name = inspect_data.get("Name", "").lstrip("/")

        image_full = inspect_data.get("Config", {}).get("Image", "")
        image_name, image_tag = image_full.split(":") if ":" in image_full else (image_full, "latest")

        ports = inspect_data.get("NetworkSettings", {}).get("Ports", {})
        docker_port = next(iter(ports.keys()), "")

        docker_status = inspect_data.get("State", {}).get("Status", "unknown")
        docker_version = inspect_data.get("Config", {}).get("Labels", {}).get("org.opencontainers.image.version", "")

        env = inspect_data.get("Config", {}).get("Env", [])

        return cls(
            container_id=container_id,
            container_name=container_name,
            image_name=image_name,
            image_tag=image_tag,
            docker_port=docker_port,
            docker_status=docker_status,
            vllm_status="starting",
            docker_version=docker_version,
            env=env,
            devices=devices,
        )


@dataclass
class GPUInfo:
    index: int
    name: str = ""
    memory_used: int = 0
    memory_total: int = 0
    utilization: int = 0

    def __init__(
        self,
        index: str,
        name: str = "",
        memory_used: int = 0,
        memory_total: int = 0,
        utilization: int = 0,
    ):
        self.index = int(index)
        self.name = name
        self.memory_used = memory_used
        self.memory_total = memory_total
        self.utilization = utilization

    def _fetch_gpu_info(self):
        import subprocess

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
                if len(parts) == 5 and int(parts[0]) == self.index:
                    self.name = parts[1]
                    self.memory_used = int(parts[2])
                    self.memory_total = int(parts[3])
                    self.utilization = int(parts[4])
                    return

        except subprocess.CalledProcessError as e:
            print(f"Failed to query nvidia-smi: {e}")


class TableRow(Base):
    __tablename__ = "table_row"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    env_info: Mapped[str] = mapped_column(Text, nullable=False)
    model_info: Mapped[str] = mapped_column(Text, nullable=False)
    user_info: Mapped[str] = mapped_column(Text, nullable=False)
    docker_info: Mapped[str] = mapped_column(Text, nullable=True)
    gpu_infos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vllm_health: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vllm_stats: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
