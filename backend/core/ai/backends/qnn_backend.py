"""Capability-detected Qualcomm QNN/ONNX Runtime adapter."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
from pathlib import Path


@dataclass
class QnnCapability:
    available: bool
    provider: str
    model_path: str | None
    reason: str
    initialized: bool = False

    def as_dict(self):
        return asdict(self)


class QnnBackend:
    name = "QNN_ONNX_RUNTIME"

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path
        self.session = None
        self.capability = self.probe(model_path)
        if self.capability.available and model_path:
            try:
                import onnxruntime as ort
                self.session = ort.InferenceSession(model_path, providers=["QNNExecutionProvider", "CPUExecutionProvider"])
                self.capability.initialized = True
            except Exception as exc:
                self.capability = QnnCapability(False, "QNNExecutionProvider", model_path, f"Model session initialization failed: {type(exc).__name__}.")

    @staticmethod
    def probe(model_path: str | None) -> QnnCapability:
        if importlib.util.find_spec("onnxruntime") is None:
            return QnnCapability(False, "QNNExecutionProvider", model_path, "onnxruntime is not installed.")
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
        except Exception as exc:
            return QnnCapability(False, "QNNExecutionProvider", model_path, f"onnxruntime could not enumerate providers: {type(exc).__name__}.")
        if "QNNExecutionProvider" not in providers:
            return QnnCapability(False, "QNNExecutionProvider", model_path, "QNNExecutionProvider is not present in this ONNX Runtime installation.")
        if not model_path:
            return QnnCapability(False, "QNNExecutionProvider", None, "A validated ONNX model path is required.")
        if not Path(model_path).is_file():
            return QnnCapability(False, "QNNExecutionProvider", model_path, "Configured ONNX model was not found.")
        return QnnCapability(True, "QNNExecutionProvider", model_path, "QNN provider and model path are available.")

    def health_check(self) -> dict:
        return self.capability.as_dict()

    def generate(self, _prompt: str, **_kwargs):
        raise RuntimeError("QNN text generation requires a validated model-specific adapter; this ONNX session is not treated as a generic LLM.")
