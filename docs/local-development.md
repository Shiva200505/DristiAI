# Local development

Core dependencies are intentionally small: FastAPI, Uvicorn, SQLAlchemy, Pydantic, and psutil. Optional tools are not required for the deterministic demo.

Useful variables:

```text
DRISHTI_LOCAL_ONLY=true
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

Semantic retrieval is enabled only when `DRISHTI_EMBEDDING_MODEL` points to a locally available Sentence Transformers model. With no model installed, the index reports `NO_EMBEDDING_MODEL` and uses clearly labeled lexical matching; the hash-vector smoke fallback is opt-in only.
