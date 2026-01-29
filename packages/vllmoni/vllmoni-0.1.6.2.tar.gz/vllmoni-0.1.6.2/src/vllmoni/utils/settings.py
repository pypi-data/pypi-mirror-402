import os
from pathlib import Path


def get_settings() -> dict:
    # Use environment variable if set
    db_path = os.environ.get("VLLMONI_DB_PATH")

    if not db_path:
        # Default writable location in user home
        default_dir = Path.home() / ".vllmoni"
        default_dir.mkdir(parents=True, exist_ok=True)
        db_path = f"sqlite:///{default_dir}/vllmoni.db"

    return {
        "db_path": db_path,
    }
