import json
from dataclasses import asdict, dataclass
from pathlib import Path
from backend.config import settings


@dataclass
class Document:
    text: str
    source: str
    file: str
    section: str = ""


class LocalVectorStore:
    """Dependency-free local retrieval seam; ChromaDB can replace the storage adapter later."""
    def __init__(self, project_slug: str = "default"):
        self.path = settings.root / ".drishti" / f"index-{project_slug}.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.documents: list[Document] = []
        if self.path.exists():
            self.documents = [Document(**item) for item in json.loads(self.path.read_text(encoding="utf-8"))]

    def add_documents(self, documents: list[Document]) -> None:
        self.documents.extend(documents)
        self.path.write_text(json.dumps([asdict(item) for item in self.documents], indent=2), encoding="utf-8")

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        tokens = {token.lower() for token in query.split() if len(token) > 2}
        ranked = []
        for document in self.documents:
            score = sum(token in document.text.lower() for token in tokens)
            if score:
                ranked.append((score, document))
        return [{**asdict(document), "distance": round(1 / (score + 1), 3)} for score, document in sorted(ranked, key=lambda item: item[0], reverse=True)[:n_results]]

    def stats(self) -> dict:
        return {"doc_count": len(self.documents), "chunk_count": len(self.documents), "size_bytes": self.path.stat().st_size if self.path.exists() else 0}
