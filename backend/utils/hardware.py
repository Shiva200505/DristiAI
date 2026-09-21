from dataclasses import asdict, dataclass
import importlib.util
import os
import platform
import psutil


@dataclass
class DeviceInfo:
    os: str
    arch: str
    processor: str
    ram_gb: float
    active_backend: str
    npu_available: bool
    npu_detail: str
    gpu_available: bool
    gpu_name: str
    snapdragon_detected: bool
    device_label: str


def detect_hardware() -> DeviceInfo:
    processor = platform.processor() or platform.machine()
    qnn = False
    if importlib.util.find_spec("onnxruntime"):
        try:
            import onnxruntime
            qnn = any("QNN" in provider.upper() for provider in onnxruntime.get_available_providers())
        except Exception:
            qnn = False
    snapdragon = "snapdragon" in processor.lower() or "qualcomm" in processor.lower()
    return DeviceInfo(platform.platform(), platform.machine(), processor, round(psutil.virtual_memory().total / 1024**3, 2), "QNN" if qnn else "CPU", qnn, "QNN provider detected" if qnn else "Not measured on Snapdragon hardware", False, "Unknown", snapdragon and qnn, "SNAPDRAGON_DEVICE" if snapdragon and qnn else "DEV_MACHINE")


def hardware_payload() -> dict:
    return asdict(detect_hardware())


def memory_info() -> dict:
    memory = psutil.virtual_memory()
    return {"total_gb": round(memory.total / 1024**3, 2), "used_gb": round(memory.used / 1024**3, 2), "percent": memory.percent}
