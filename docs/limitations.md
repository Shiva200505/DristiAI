# Honest limitations

- Bandit, Semgrep, ChromaDB, and a local LLM are optional dependencies; the product runs with deterministic local fallback rules when they are missing.
- The current VS Code extension sends saved file content to `127.0.0.1` only. It does not implement a remote language server.
- The included Node UI and FastAPI service are parallel demo surfaces while the architecture is being converged; the competition submission should choose one process supervisor.
- No Snapdragon hardware measurement is included in this repository.
