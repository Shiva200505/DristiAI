from fastapi import APIRouter
from backend.core.ai.model_registry import ModelRegistry
from backend.utils.hardware import hardware_payload, memory_info

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/hardware")
def hardware():
    return {"device": hardware_payload(), "memory": memory_info(), "measurement_source": "DEV_MACHINE"}


@router.get("/runtime")
def runtime():
    registry = ModelRegistry()
    return {**registry.status(), "llm_available": registry.llm_available, "measurement_source": "DEV_MACHINE"}


@router.get("/privacy")
def privacy():
    return {"local_only": True, "network_policy": "loopback-only unless an operator explicitly enables dependency/provider network access", "external_egress": "NOT_MEASURED", "egress_bytes": None, "external_services": {"llm": False, "analytics": False, "profiling": False}, "last_network_event": "No external network event recorder is configured"}
