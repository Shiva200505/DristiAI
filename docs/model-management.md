# Model management

Model files are operator-installed artifacts. Drishti does not silently download or execute them. Before enabling a model, record its source, version, format, checksum, size, runtime, precision, and intended device.

`/api/system/runtime` reports the active provider and health. `TEMPLATE_FALLBACK` means no generative model is installed; it does not mean AI ran. A future installer can add checksum verification and model metadata without changing the provider interface.

## CPU GGUF path

1. Install the optional `llama-cpp-python` package in the project virtual environment.
2. Place a trusted local GGUF file on disk; do not commit it or paste its contents into source control.
3. Set `DRISHTI_MODEL_PATH` to the file and optionally set `DRISHTI_MODEL_ID`.
4. Run `npm run models:validate -- --path C:\models\model.gguf`, then `npm run doctor`.
5. Restart FastAPI and confirm `/api/system/runtime` reports `CPU_LLAMA_CPP` and a real model path.

## Local GenieX path

GenieX is a separate operator-installed local service. Start it on loopback, set `DRISHTI_GENIEX_BASE_URL` and `DRISHTI_MODEL_ID`, then run `npm run doctor`. With `DRISHTI_LOCAL_ONLY=true`, non-loopback GenieX URLs are blocked. No cloud API key is required by Drishti for this path.

## Embeddings

Set `DRISHTI_EMBEDDING_MODEL` to a locally available Sentence Transformers model and keep `DRISHTI_ALLOW_MODEL_DOWNLOAD=false` for offline operation. Without it, retrieval remains lexical and is labeled `NO_EMBEDDING_MODEL`.

Qualcomm AI Hub/Workbench credentials belong in the operator's Qualcomm CLI configuration, not Drishti environment variables, browser settings, or repository files. See [the Qualcomm validation path](qualcomm.md).
