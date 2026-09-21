from pathlib import Path
from backend.core.retrieval.vector_store import Document, LocalVectorStore


def index_path(path: str | Path, store: LocalVectorStore | None = None) -> int:
    root = Path(path)
    store = store or LocalVectorStore(root.name)
    documents = []
    for file in root.rglob("*") if root.is_dir() else [root]:
        if file.is_file() and file.suffix.lower() in {".md", ".txt", ".py", ".js", ".ts", ".yaml", ".yml"}:
            try:
                text = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for index in range(0, len(text), 1600):
                documents.append(Document(text=text[index:index + 1600], source="local-file", file=str(file), section=f"chunk-{index // 1600 + 1}"))
    store.add_documents(documents)
    return len(documents)
