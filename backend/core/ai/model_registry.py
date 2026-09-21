from dataclasses import dataclass
from enum import Enum
import importlib.util
import os
import platform


class InferenceBackend(str, Enum):
    CPU_LLAMA_CPP = "CPU_LLAMA_CPP"
    CPU_TRANSFORMERS = "CPU_TRANSFORMERS"
    QNN_ONNX_RUNTIME = "QNN_ONNX_RUNTIME"
    QNN_GENIEX = "QNN_GENIEX"
    TEMPLATE_FALLBACK = "TEMPLATE_FALLBACK"


@dataclass(frozen=True)
class DeviceInfo:
    backend: InferenceBackend
    model_path: str | None
    machine: str
    note: str


class ModelRegistry:
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or os.getenv("DRISHTI_MODEL_PATH")
        self.device = self._detect()

    def _detect(self) -> DeviceInfo:
        if self.model_path and importlib.util.find_spec("llama_cpp"):
            return DeviceInfo(InferenceBackend.CPU_LLAMA_CPP, self.model_path, platform.processor() or platform.machine(), "Local GGUF model configured; measured on development machine")
        return DeviceInfo(InferenceBackend.TEMPLATE_FALLBACK, None, platform.processor() or platform.machine(), "No local LLM configured; deterministic fallback is active")

    @property
    def llm_available(self) -> bool:
        return self.device.backend == InferenceBackend.CPU_LLAMA_CPP

    def get_llm(self):
        if not self.llm_available:
            return None
        from backend.core.ai.backends.cpu_backend import CpuLlamaBackend
        return CpuLlamaBackend(self.device.model_path)
