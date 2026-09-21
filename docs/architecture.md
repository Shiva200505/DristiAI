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

`server.mjs` remains the browser-facing realtime gateway because it owns the existing working UI, file watcher, SSE heartbeat, and demo state. `backend/` is the canonical typed service for integrations, persistence, project/dependency scans, knowledge indexing, model status, and safe patch APIs. The two paths do not define separate security rules: the Python service is the reference contract for new integrations, while the Node engine preserves the existing offline browser demo.

SQLite is local persistence. Additive schema migration keeps MVP databases readable. Audit events contain event metadata, not prompts, secrets, or full source copies.

## Boundaries

- Deterministic rules and external scanners create evidence.
- AI can explain or propose; it cannot mark a finding verified.
- Patch application is a separate explicit operation with a SHA-256 precondition.
- Verification rescans the candidate and checks syntax before reporting `VERIFIED_RESOLVED`.
- Runtime labels come from provider detection, not from UI configuration alone.
