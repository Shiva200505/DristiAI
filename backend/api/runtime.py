import json
from pathlib import Path
from fastapi import APIRouter
from backend.core.ai.model_registry import ModelRegistry
from backend.utils.hardware import hardware_payload, memory_info

router = APIRouter(prefix="/api", tags=["runtime"])


@router.get("/models")
def models():
    registry = ModelRegistry()
    return {"items": [registry.status()]}


@router.get("/performance")
def performance():
    return {"measurement_source": "DEV_MACHINE", "hardware": hardware_payload(), "memory": memory_info(), "metrics": {"npu": {"status": "NOT_MEASURED_ON_SNAPDRAGON_HARDWARE"}, "gpu": {"status": "NOT_MEASURED_ON_SNAPDRAGON_HARDWARE"}}}


@router.get("/benchmarks")
def benchmarks():
    results_dir = Path(__file__).resolve().parents[2] / "benchmarks" / "results"
    items = []
    for path in sorted(results_dir.glob("*.json"), reverse=True) if results_dir.is_dir() else []:
        try:
            items.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return {"items": items[:50], "source": "stored benchmark JSON", "measurement_policy": "Only recorded measurements are returned."}
