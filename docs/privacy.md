# Privacy

Local-only mode keeps source analysis, SQLite history, retrieval, patches, and fallback explanations on the machine. The app does not send source to a cloud AI service. Optional model downloads and OSV-Scanner network access require explicit setup/configuration and are separate from the core workflow.

Logs avoid full source, prompts, and secret values. Finding evidence masks credential-like literals. The privacy API exposes configured mode and external-service flags; it does not make legal compliance claims.
