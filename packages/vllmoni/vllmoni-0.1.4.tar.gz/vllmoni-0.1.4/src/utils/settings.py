from pathlib import Path


def get_settings() -> dict:
    import toml

    base_dir = Path(__file__).parent.parent.parent.resolve()
    config_path = base_dir / "pyproject.toml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config = toml.load(config_path)
    return config.get("tool", {}).get("vllmoni", {})
