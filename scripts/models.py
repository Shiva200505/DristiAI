"""Explicit model inventory and diagnostics.

This command never downloads model weights. Model installation is an operator
decision and must remain visible, checksumable, and local-first.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import socket
import sys
from urllib.request import urlopen
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.core.ai.model_registry import ModelRegistry
from backend.core.ai.embedder import LocalEmbedder
from backend.core.security.ast_analysis import ast_capabilities


def check(name: str, available: bool, detail: str, optional: bool = True, status: str | None = None) -> dict:
    return {"name": name, "status": status or ("available" if available else ("optional_unavailable" if optional else "broken")), "detail": detail}


def doctor() -> dict:
    registry = ModelRegistry()
    runtime = registry.status()
    embedding = LocalEmbedder().metadata()
    ast_status = ast_capabilities()
    geniex_available = _geniex_health()
    qnn_available = _qnn_available()
    checks = [
        check("node", shutil.which("node") is not None, shutil.which("node") or "Node.js is not on PATH", optional=False),
        check("python", True, platform.python_version(), optional=False),
        check("sqlite", importlib.util.find_spec("sqlite3") is not None, "Python sqlite3 module"),
        check("bandit", shutil.which("bandit") is not None, "Install bandit to enable Python third-party rules"),
        check("semgrep", shutil.which("semgrep") is not None, "Install semgrep to enable Semgrep rules"),
        check("osv-scanner", shutil.which("osv-scanner") is not None, "Install OSV-Scanner and explicitly allow its network/database path"),
        check("tree-sitter", ast_status["tree_sitter"]["executed"], "Tree-sitter grammar is wired" if ast_status["tree_sitter"]["executed"] else "Tree-sitter module is installed but no grammar/adapter is wired"),
        check("embedding-model", embedding["semantic"], f"{embedding['backend']}: {embedding['model']}"),
        check("llm", bool(runtime.get("llm_available")), f"{runtime.get('backend')}: {runtime.get('note') or runtime.get('reason') or runtime.get('model_id') or 'no local model'}"),
        check("llama.cpp", importlib.util.find_spec("llama_cpp") is not None, "llama_cpp module is installed; configure DRISHTI_MODEL_PATH" if importlib.util.find_spec("llama_cpp") else "Install llama-cpp-python and configure DRISHTI_MODEL_PATH"),
        check("geniex", geniex_available, "GenieX /v1/models responded" if geniex_available else "Configure DRISHTI_GENIEX_BASE_URL and start its local service"),
        check("onnxruntime-qnn", qnn_available, "QNNExecutionProvider is available" if qnn_available else "Install a compatible ONNX Runtime build with QNNExecutionProvider"),
        check("workspace", ROOT.is_dir() and os.access(ROOT, os.R_OK | os.W_OK), str(ROOT), optional=False),
        check("backend-port", _port_open("127.0.0.1", 8000), "FastAPI loopback service"),
        check("ui-port", _port_open("127.0.0.1", 4173), "Node realtime gateway"),
    ]
    checks.append(check("python-ast", ast_capabilities()["python_ast"]["installed"], "stdlib ast analyzer", optional=False))
    return {"platform": {"os": platform.platform(), "machine": platform.machine(), "python": platform.python_version()}, "runtime": runtime, "embedding": embedding, "checks": checks}


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False


def _geniex_health() -> bool:
    base_url = os.getenv("DRISHTI_GENIEX_BASE_URL", "").rstrip("/")
    if not base_url:
        return False
    try:
        with urlopen(f"{base_url}/v1/models", timeout=1.5) as response:
            return response.status == 200
    except OSError:
        return False


def _qnn_available() -> bool:
    if importlib.util.find_spec("onnxruntime") is None:
        return False
    try:
        import onnxruntime as ort
        return "QNNExecutionProvider" in ort.get_available_providers()
    except Exception:
        return False


def model_list() -> dict:
    registry = ModelRegistry()
    return {"items": [registry.status()], "install_policy": "operator-installed; no automatic downloads"}


def validate(path: str | None = None) -> dict:
    model_path = Path(path or os.getenv("DRISHTI_MODEL_PATH", "")).expanduser() if (path or os.getenv("DRISHTI_MODEL_PATH")) else None
    if not model_path:
        return {"status": "NOT_CONFIGURED", "message": "Set DRISHTI_MODEL_PATH to a local model file before validation."}
    if not model_path.is_file():
        return {"status": "INVALID", "path": str(model_path), "message": "Configured model file does not exist."}
    digest = hashlib.sha256()
    with model_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"status": "VALIDATED_FILE", "path": str(model_path), "bytes": model_path.stat().st_size, "sha256": digest.hexdigest(), "format": model_path.suffix.lower().lstrip(".") or "unknown", "note": "File integrity was checked; provider initialization still occurs when FastAPI starts."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Drishti local model and runtime diagnostics")
    parser.add_argument("command", choices=["list", "validate", "doctor"])
    parser.add_argument("--path", help="Model file path for validate")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    payload = model_list() if args.command == "list" else validate(args.path) if args.command == "validate" else doctor()
    print(json.dumps(payload, indent=2, default=str))
    return 0 if args.command != "validate" or payload.get("status") in {"NOT_CONFIGURED", "VALIDATED_FILE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
