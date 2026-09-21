# Drishti AI

Private, local-first security engineering for developers: detect → understand → fix → verify.

This repository contains a self-contained product demo with a zero-dependency Node runtime. It runs on a normal Windows development machine and reports the active execution backend honestly as `CPU / Development`. Snapdragon/QNN adapters are intentionally represented as a future deployment boundary rather than fabricated hardware measurements.

The 9-day competition path is now scaffolded in parallel: FastAPI at port 8000, a VS Code save listener, eight vulnerable demo samples, real benchmark scripts, and an optional Electron desktop shell.

## Run locally

```powershell
npm start
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://localhost:4173. The app uses an in-memory local demo store; restarting the server resets the sample workspace.

## Test

```powershell
npm test
python -m unittest tests.test_backend -v
python scripts/demo_prep.py
```

## Product slice included

- Command center with posture, recent findings, live pipeline, and audit activity.
- Deterministic local security engine for SQL injection, command injection, hardcoded secrets, and XSS sinks.
- Finding detail, candidate patch review, controlled apply, and explicit verification states.
- Live Security editor with scan action and evidence lines.
- Realtime local event stream (SSE) for findings, scan stages, activity, source updates, and runtime telemetry.
- Watched `workspace/services/auth.py` file: external edits trigger a local scan automatically.
- Source editor can save code to the watched workspace file and immediately run the scan pipeline.
- Local Knowledge, Ask Drishti, Performance, Privacy Center, and Settings views.
- Honest runtime labeling: CPU development backend, offline/local-only state, and unmeasured Snapdragon metrics.

## Architecture boundary

`public/` is the UI. `src/security-engine.mjs` is the deterministic analyzer and patch contract. `server.mjs` provides local API routes, an SSE event stream, file watching, and a small local JSON persistence seam under `.drishti/`. The runtime object is the intended adapter point for a later ONNX Runtime QNN or Qualcomm AI Runtime implementation.

## Realtime behavior

The browser opens `/api/events` as a local Server-Sent Events stream. The server broadcasts `scan:start`, `scan:stage`, `scan:complete`, `findings`, `activity`, `source:update`, and `runtime` events. The sample workspace file is watched with the Node filesystem watcher, so changing `workspace/services/auth.py` outside the UI also triggers analysis.

The working security layer is deterministic and local today; it does not require a cloud service or downloaded model. A semantic model is an optional next adapter, not a hidden dependency. To add it properly, the project will need a local model artifact plus its supported runtime (for example an ONNX/CPU adapter during development, then a validated QNN/Qualcomm runtime on Snapdragon hardware). No Snapdragon performance number is claimed until that runtime is actually measured.
