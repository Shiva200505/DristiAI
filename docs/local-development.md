# Local development

Core dependencies are intentionally small: FastAPI, Uvicorn, SQLAlchemy, Pydantic, and psutil. Optional tools are not required for the deterministic demo.

Useful variables:

```text
DRISHTI_LOCAL_ONLY=true
DRISHTI_WORKSPACE_ROOT=C:\your\actual\repository
DRISHTI_SOURCE_FILE=src\api\users.py
DRISHTI_ALLOW_EXTERNAL_WORKSPACE=true
DRISHTI_MODEL_RUNTIME=auto|geniex|qnn
DRISHTI_MODEL_ID=local-model
DRISHTI_MODEL_PATH=C:\models\model.gguf
DRISHTI_GENIEX_BASE_URL=http://127.0.0.1:18181
DRISHTI_EMBEDDING_MODEL=C:\models\all-MiniLM-L6-v2
DRISHTI_ALLOW_MODEL_DOWNLOAD=false
DRISHTI_ALLOW_OSV_NETWORK=false
DRISHTI_EMERGENCY_HASH_EMBEDDINGS=false
```

`npm run dev` starts the browser gateway on port 4173. `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000` starts the typed backend. `.drishti/` contains local SQLite, indexes, and rollback files and is ignored by Git.

For a real repository, replace `C:\your\actual\repository` with an existing path and set `DRISHTI_WORKSPACE_ROOT` in both terminals before starting either service. Set `DRISHTI_SOURCE_FILE` to a path relative to that root, for example `src\api\users.py`. The Node gateway watches the workspace recursively for supported source extensions (`.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.java`, `.go`, `.rb`, `.php`, `.rs`, `.c`, `.cpp`, `.cs`, `.sql`, `.html`, `.vue`, `.svelte`, `.kt`, `.swift`, `.sh`, `.bash`, `.yaml`, `.yml`, `.json`). `Scan now` scans the workspace; `Run analysis` scans only the selected file. If the workspace is outside this repository, keep `DRISHTI_ALLOW_EXTERNAL_WORKSPACE=true` for the FastAPI project/index routes. If the old example value `C:\path\to\your\repository` is used accidentally, the gateway falls back to the included `workspace/` directory and prints a warning.

For a quick capability check, run `npm run doctor`, `npm run models:list`, and `npm run models:validate`. The default path needs no model and truthfully uses deterministic explanations. Start both services before opening the browser; the gateway calls the backend through `DRISHTI_BACKEND_URL` when a non-default backend port is used.

Semantic retrieval is enabled only when `DRISHTI_EMBEDDING_MODEL` points to a locally available Sentence Transformers model. With no model installed, the index reports `NO_EMBEDDING_MODEL` and uses clearly labeled lexical matching; the hash-vector smoke fallback is opt-in only.
