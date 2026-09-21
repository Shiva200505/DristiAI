from pathlib import Path
import os
from backend.core.retrieval.vector_store import Document, LocalVectorStore


def index_path(path: str | Path, store: LocalVectorStore | None = None) -> int:
    root = Path(path).resolve()
    store = store or LocalVectorStore(root.name)
    documents = []
    excluded = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".drishti", ".pytest_cache"}
    allowed_suffixes = {".md", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx", ".yaml", ".yml", ".json", ".toml", ".xml"}
    max_bytes = int(os.getenv("DRISHTI_INDEX_MAX_FILE_BYTES", str(512 * 1024)))
    for file in root.rglob("*") if root.is_dir() else [root]:
        if file.is_file() and file.suffix.lower() in allowed_suffixes and not excluded.intersection({part.lower() for part in file.parts}) and file.stat().st_size <= max_bytes:
            try:
                text = file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for index in range(0, len(text), 1600):
                documents.append(Document(text=text[index:index + 1600], source="local-file", file=str(file.relative_to(root)) if root.is_dir() else str(file), section=f"chunk-{index // 1600 + 1}", metadata={"bytes": file.stat().st_size}))
    store.add_documents(documents)
    return len(documents)
