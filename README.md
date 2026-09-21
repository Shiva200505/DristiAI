# Drishti AI

Private, local-first security engineering for developers: **detect → understand → fix → verify**.

Drishti is an actual local workflow, not a chatbot mockup. It scans source code with deterministic rules and optional Bandit/Semgrep adapters, inventories dependencies, explains evidence, creates reviewable candidate patches, applies only explicitly approved changes with a content fingerprint and rollback copy, and verifies the result with a rescan and syntax checks.

## What is real today

- Browser workspace with live SSE events, file watching, source editing, finding detail, patch review, verification, local knowledge, runtime, and privacy views.
- Canonical Python security services under `backend/`: finding normalization, project/incremental scanning, dependency inventory/OSV-Scanner integration, retrieval, model providers, patch safety, verification, persistence, and typed API routes.
- Deterministic coverage for SQL injection, command injection, path traversal, secrets, weak cryptography, insecure deserialization, XSS, and SSRF-related sinks in Python/JavaScript/TypeScript.
- Optional real tools: Bandit, Semgrep, OSV-Scanner, llama.cpp, Sentence Transformers, and ONNX Runtime QNN. Missing tools produce an explicit capability state.
- VS Code save-triggered diagnostics integration and an eight-fixture demo repository.

## Runtime truthfulness

The default development machine needs no model download. It reports `TEMPLATE_FALLBACK` for explanation and uses deterministic evidence. A real local GGUF model is selected only when `DRISHTI_MODEL_PATH` and `llama-cpp-python` are both present. A local GenieX server is selected only when `DRISHTI_GENIEX_BASE_URL` is configured. QNN is selected only after ONNX Runtime reports `QNNExecutionProvider` and a configured model can be initialized.

No Snapdragon utilization, watts, token rate, or latency is invented. Until a physical or remote Snapdragon run is imported, the product says **NOT MEASURED ON SNAPDRAGON HARDWARE**.

## Quick start on Windows

```powershell
git clone https://github.com/Shiva200505/DristiAI.git
cd DristiAI
npm install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the browser UI and FastAPI service in two terminals:

```powershell
npm run dev
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open `http://localhost:4173`. The browser UI is the realtime local workspace; FastAPI is the typed integration/persistence API used by VS Code and automation. See [local development](docs/local-development.md) for environment variables and model setup.

## Verification commands

```powershell
npm run build
npm test
npm run test:backend
python scripts/demo_prep.py
npm run benchmark
```

`npm run verify` runs the complete local smoke sequence. Optional tools are detected at runtime and are never silently reported as having run when unavailable.

## API examples

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/system/runtime
curl -X POST http://127.0.0.1:8000/api/scans/project -H "Content-Type: application/json" -d '{"project_root":"demo-repo","use_external_tools":false}'
curl -X POST http://127.0.0.1:8000/api/scans/dependencies -H "Content-Type: application/json" -d '{"project_root":".","allow_network":false}'
```

## Architecture

The browser entrypoint remains the existing polished Node/SSE workspace so the demo stays reliable. The backend has one canonical security core and typed FastAPI boundary for persistence, VS Code, project scans, dependency scans, knowledge indexing, model/runtime status, and patch operations. The Node server owns browser session events and delegates no security claim to the UI. Details are in [architecture](docs/architecture.md) and [AI architecture](docs/ai-architecture.md).

## Documentation

- [Local development](docs/local-development.md)
- [Security engine](docs/security-engine.md)
- [Patch verification](docs/patch-verification.md)
- [Qualcomm path](docs/qualcomm.md)
- [Snapdragon deployment](docs/snapdragon-deployment.md)
- [Model management](docs/model-management.md)
- [Privacy](docs/privacy.md)
- [Threat model](docs/threat-model.md)
- [VS Code extension](docs/vscode-extension.md)
- [Benchmarking](docs/benchmarking.md)
- [Demo guide](docs/demo-guide.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Limitations](docs/limitations.md)

## Project language

Drishti is not a guarantee of security or legal compliance. Findings are evidence for engineering review. AI output is untrusted until a developer reviews the diff and verification result. Qualcomm, Snapdragon, QNN, AI Hub, and GenieX references describe supported deployment paths and are not an endorsement or partnership claim.
