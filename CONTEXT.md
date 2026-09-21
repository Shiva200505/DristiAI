# Drishti AI Context

Drishti AI is a local-first developer security workspace for the Snapdragon AI Lab Build & Present Challenge 2026.

## Current architecture

- `server.mjs` + `public/`: the runnable realtime UI demo on port 4173. It exposes an SSE stream at `/api/events`, watches `workspace/services/auth.py`, and owns the immediate detect → patch → verify experience.
- `backend/`: the competition-oriented FastAPI service on port 8000. It owns typed scan, finding, patch, chat, project, hardware, and benchmark APIs. It is deliberately dependency-tolerant: Bandit, Semgrep, ChromaDB, and a local LLM are optional and are reported as unavailable when not installed.
- `vscode-extension/`: the primary IDE integration. Save events are debounced and posted to the FastAPI `/api/scans/trigger` endpoint.
- `demo-repo/`: intentionally vulnerable samples used for the judge demonstration.

## Truthfulness rules

Never claim NPU utilization, Snapdragon latency, QNN execution, model availability, or power draw unless the runtime reports a real measurement. Development values must say `DEV_MACHINE`; unavailable Snapdragon values must say `NOT_MEASURED_ON_SNAPDRAGON_HARDWARE`.

## Local model boundary

The security pipeline works without a model. `DRISHTI_MODEL_PATH` enables an optional local `llama-cpp-python` provider; otherwise the explainer returns a clearly labelled deterministic fallback. No cloud LLM is used.

## Commands

```powershell
npm start
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
python scripts/demo_prep.py
python benchmarks/run_benchmarks.py --component scanner
npm test
```
