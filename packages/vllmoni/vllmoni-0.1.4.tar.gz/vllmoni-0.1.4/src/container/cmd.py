import random
from typing import Optional

from app.models import EnvInfo, ModelInfo, UserInfo


def create_docker_command(
    model: ModelInfo,
    env_info: EnvInfo,
    env_vars: dict,
    user_info: UserInfo,
    extra_args: Optional[list[str]] = None,
) -> list[str]:
    cmd = docker_run_base()
    cmd += add_name(user_info.user_name, model.model_name_short, model.seed)
    cmd += add_runtime()

    for key, value in env_vars.items():
        cmd += add_env_var(key, value)

    cmd += add_port(env_info.port)
    cmd = add_gpus(cmd, env_info.devices)
    cmd += add_ipc()
    cmd += add_image_and_tag(env_info)
    cmd += add_model_flags(model, env_vars["VLLM_API_KEY"])
    cmd = add_dtype(cmd, model.dtype)

    # Optional VLLM flags
    cmd = add_enforce_eager(cmd, model.enforce_eager)
    cmd = add_volume(cmd, env_vars)
    cmd = add_gpu_utilization(cmd, model)
    cmd = add_tool_support(cmd, model)
    cmd = add_tokenizer(cmd, model.tokenizer)
    cmd = add_max_model_len(cmd, model.max_model_len)
    cmd = add_tensor_parallel_size(cmd, model.tensor_parallel_size)
    cmd = add_trust_remote_code(cmd, model.trust_remote_code)
    cmd = add_disable_log_requests(cmd, model.disable_log_requests)
    cmd = add_disable_log_stats(cmd, model.disable_log_stats)
    cmd = add_max_concurrent_requests(cmd, model.max_concurrent_requests)
    cmd = add_max_log_len(cmd, model.max_log_len)
    cmd = add_seed(cmd, model.seed)
    cmd = add_max_num_seqs(cmd, model.max_num_seqs)
    cmd = add_disable_deployment_check(cmd, model.disable_deployment_check)
    cmd = add_no_enable_prefix_caching(cmd, model.no_enable_prefix_caching)

    # Extra user-defined args
    cmd = add_extra_args(cmd, extra_args)

    return cmd


def add_env_var(key: str, value: str) -> list[str]:
    return ["--env", f"{key}={value}"]


def add_gpu_utilization(cmd: list[str], model: ModelInfo) -> list[str]:
    if model.gpu_memory_utilization is not None:
        return cmd + ["--gpu-memory-utilization", str(model.gpu_memory_utilization)]
    return cmd


def add_gpus(cmd: list[str], devices: Optional[str]) -> list[str]:
    if str(devices) not in ["None", "null", ""]:
        return cmd + ["--gpus", f"device={devices}"]
    return cmd + ["--gpus", "all"]


def add_image(image: str, tag: str) -> list[str]:
    return [f"{image}:{tag}"]


def add_image_and_tag(env_info: EnvInfo) -> list[str]:
    return [f"{env_info.image_name}:{env_info.image_tag}"]


def add_ipc() -> list[str]:
    return ["--ipc=host"]


def add_model_flags(model: ModelInfo, api_key: str) -> list[str]:
    return [
        "--model",
        model.model_name,
        "--api-key",
        api_key,
    ]


def add_dtype(cmd: list[str], dtype: Optional[str]) -> list[str]:
    if dtype:
        return cmd + ["--dtype", dtype]
    else:
        return cmd + ["--dtype", "auto"]


def add_enforce_eager(cmd: list[str], enforce: bool) -> list[str]:
    if enforce:
        return cmd + ["--enforce-eager"]
    return cmd


def add_name(user_name: str, model_short_name: str, seed: Optional[int]) -> list[str]:
    # Format: vllmoni_{user_name}_{model_short_name}_{seed}
    # Docker container names must match: [a-zA-Z0-9][a-zA-Z0-9_.-]*
    # Sanitize user_name and model_short_name to ensure Docker compatibility
    safe_user_name = "".join(c if c.isalnum() or c in "_-." else "_" for c in user_name)
    safe_model_name = "".join(c if c.isalnum() or c in "_-." else "_" for c in model_short_name)

    if seed is not None:
        # Use the provided seed (including seed=0)
        container_name = f"vllmoni_{safe_user_name}_{safe_model_name}_{seed}"
    else:
        # If no seed is provided, use a random number
        container_name = f"vllmoni_{safe_user_name}_{safe_model_name}_{random.randint(100, 999)}"
    return ["--name", container_name]


def add_port(port: int) -> list[str]:
    return ["-p", f"{port}:8000"]


def add_runtime() -> list[str]:
    return ["--runtime", "nvidia"]


def add_tool_support(cmd: list[str], model: ModelInfo) -> list[str]:
    if model.tool_call_parser is not None:
        return cmd + [
            "--enable-auto-tool-choice",
            "--tool-call-parser",
            model.tool_call_parser,
        ]
    return cmd


def add_volume(cmd: list[str], env_vars: dict) -> list[str]:
    path = env_vars.get("HF_VOLUME")
    if path:
        cmd += ["-v", path]
    return cmd


def docker_run_base() -> list[str]:
    return ["docker", "run", "-d"]


def add_tokenizer(cmd: list[str], tokenizer: Optional[str]) -> list[str]:
    if tokenizer:
        return cmd + ["--tokenizer", tokenizer]
    return cmd


def add_max_model_len(cmd: list[str], length: Optional[int]) -> list[str]:
    if length:
        return cmd + ["--max-model-len", str(length)]
    return cmd


def add_tensor_parallel_size(cmd: list[str], size: Optional[int]) -> list[str]:
    if size:
        return cmd + ["--tensor-parallel-size", str(size)]
    return cmd


def add_trust_remote_code(cmd: list[str], trust: bool = False) -> list[str]:
    if trust:
        return cmd + ["--trust-remote-code"]
    return cmd


def add_disable_log_requests(cmd: list[str], disable: bool = False) -> list[str]:
    if disable:
        return cmd + ["--disable-log-requests"]
    return cmd


def add_disable_log_stats(cmd: list[str], disable: bool = False) -> list[str]:
    if disable:
        return cmd + ["--disable-log-stats"]
    return cmd


def add_max_concurrent_requests(cmd: list[str], count: Optional[int]) -> list[str]:
    if count:
        return cmd + ["--max-concurrent-requests", str(count)]
    return cmd


def add_max_log_len(cmd: list[str], length: Optional[int]) -> list[str]:
    if length:
        return cmd + ["--max-log-len", str(length)]
    return cmd


def add_seed(cmd: list[str], seed: Optional[int]) -> list[str]:
    if seed is not None:
        return cmd + ["--seed", str(seed)]
    return cmd


def add_max_num_seqs(cmd: list[str], num: Optional[int]) -> list[str]:
    if num:
        return cmd + ["--max-num-seqs", str(num)]
    return cmd


def add_disable_deployment_check(cmd: list[str], disable: bool = False) -> list[str]:
    if disable:
        return cmd + ["--disable-deployment-check"]
    return cmd


def add_no_enable_prefix_caching(cmd: list[str], no_enable: bool = False) -> list[str]:
    if no_enable:
        cmd = cmd + ["--no-enable-prefix-caching"]
        # cmd = cmd + ["--no-enable-prefix-caching"]
    return cmd


def add_extra_args(cmd: list[str], extra_args: Optional[list[str]]) -> list[str]:
    if extra_args:
        return cmd + extra_args
    return cmd
