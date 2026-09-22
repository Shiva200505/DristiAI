# Architecture

The production boundary is:

```text
Browser UI / VS Code
        │ typed HTTP + SSE
FastAPI API and persistence
        │
canonical scanner → canonical findings → explainer/retrieval → patcher → verifier
        │
runtime/model providers (CPU llama.cpp, GenieX, capability-probed QNN)
```

`server.mjs` remains the browser-facing realtime gateway because it owns the existing UI, file watcher, SSE heartbeat, and browser session state. It delegates scans, explanations, chat, patch preview, patch application, and verification to the FastAPI service at `DRISHTI_BACKEND_URL`. `backend/` is the canonical typed service for security rules, persistence, project/dependency scans, knowledge indexing, model status, and safe patch APIs. If FastAPI is unavailable, the gateway reports that dependency instead of returning canned security results.

SQLite is local persistence. Additive schema migration keeps MVP databases readable. Audit events contain event metadata, not prompts, secrets, or full source copies.

## Boundaries

- Deterministic rules and external scanners create evidence.
- AI can explain or propose; it cannot mark a finding verified.
- Patch application is a separate explicit operation with a SHA-256 precondition.
- Verification rescans the candidate and checks syntax before reporting `VERIFIED_RESOLVED`; project test/typecheck commands are intentionally not run unless a trusted operator workflow adds them.
- Runtime labels come from provider detection, not from UI configuration alone.
