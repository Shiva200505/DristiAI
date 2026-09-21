# Troubleshooting

- Port in use: stop the existing Node/Uvicorn process or change the command port.
- `TEMPLATE_FALLBACK`: install a real local model and its provider deliberately; this is expected on a clean clone.
- `GENIEX_OPENAI` unavailable: start GenieX locally and verify `/v1/models`; check the configured base URL.
- `QNN_UNAVAILABLE`: inspect `/api/system/runtime`; the message names the missing provider, model, or library.
- OSV inventory only: local-only mode intentionally blocks network-backed vulnerability lookup.
- Patch rejected: the file changed after preview. Rescan and preview again; do not bypass the fingerprint.
- Empty retrieval: index the project through `/api/knowledge/index`; inspect `/api/knowledge/stats/{slug}`.
