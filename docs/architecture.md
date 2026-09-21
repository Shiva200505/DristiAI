# Drishti AI Architecture

## Demo path

VS Code save → local FastAPI `/api/scans/trigger` → deterministic fallback rules plus optional Bandit/Semgrep → explanation/patch contract → preview → explicit apply → re-scan verification. The existing realtime UI uses the same security concepts through its local Node event stream.

## Runtime boundary

The `ModelRegistry` is the only place that chooses an inference backend. Today it detects an optional local `llama-cpp-python` + GGUF model and otherwise uses a deterministic explanation fallback. A QNN/GenieX adapter is intentionally a separate integration point. The product reports `DEV_MACHINE` until a real QNN provider loads.

## Data boundary

SQLite, JSON retrieval indexes, findings, patches, and audit data live under `.drishti/`. The FastAPI service has no external network client. The UI's network indicator describes external egress, not its local loopback connection to Drishti.
