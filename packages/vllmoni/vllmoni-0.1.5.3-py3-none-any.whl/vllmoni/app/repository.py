# app/registry.py
import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from vllmoni.app.models import GPUInfo, TableRow


class ModelRepository:
    def __init__(self, session: "Session"):
        self.session = session

    def get_all(self) -> List[TableRow]:
        return self.session.query(TableRow).all()

    def get(self, model_id: int) -> TableRow | None:
        return self.session.get(TableRow, model_id)

    def create(self, table_row: TableRow) -> TableRow:
        self.session.add(table_row)
        self.session.commit()
        return table_row

    def update(self, model_id: int, **kwargs) -> None:
        model = self.get(model_id)
        if not model:
            raise ValueError("TableRow not found")
        for k, v in kwargs.items():
            setattr(model, k, v)
        model.last_updated = datetime.now(timezone.utc)
        self.session.commit()

    def update_gpu_infos(self, model_id: int, gpu_infos: list[GPUInfo]) -> None:
        model = self.get(model_id)
        if not model:
            raise ValueError("TableRow not found")
        model.gpu_infos = json.dumps([asdict(info) for info in gpu_infos])
        model.last_updated = datetime.now(timezone.utc)
        self.session.commit()

    def update_vllm_status(self, model_id: int, vllm_status: str) -> None:
        """Update the VLLM status for a model."""
        # Validate status values
        valid_statuses = ["starting", "running", "stopping", "timeout", "failed"]
        if vllm_status not in valid_statuses:
            raise ValueError(f"Invalid vllm_status: {vllm_status}. Must be one of {valid_statuses}")

        model = self.get(model_id)
        if not model:
            raise ValueError("TableRow not found")
        docker_info = json.loads(model.docker_info or "{}")
        docker_info["vllm_status"] = vllm_status
        model.docker_info = json.dumps(docker_info)
        model.last_updated = datetime.now(timezone.utc)
        self.session.commit()

    def delete(self, container_id: int) -> dict:
        try:
            model = self.get(container_id)
            if not model:
                return {"error": "Model not found", "code": 404}
            self.session.delete(model)
            self.session.commit()
            return {"status": "deleted", "container_id": container_id}
        except Exception as e:
            return {"error": str(e), "code": 500}

    def delete_all(self) -> dict:
        try:
            self.session.query(TableRow).delete()
            self.session.commit()
            return {"status": "all deleted"}
        except Exception as e:
            return {"error": str(e), "code": 500}
