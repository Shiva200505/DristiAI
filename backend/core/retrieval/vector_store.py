import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from backend.config import settings
from backend.core.ai.embedder import LocalEmbedder


@dataclass
class Document:
    text: str
    source: str
    file: str
    section: str = ""
    embedding: list[float] | None = None
    metadata: dict | None = None


class LocalVectorStore:
    """Small persisted vector index with a real-embedding provider seam."""
    def __init__(self, project_slug: str = "default"):
        self.path = settings.root / ".drishti" / f"index-{project_slug}.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.embedder = LocalEmbedder()
        self.documents: list[Document] = []
        if self.path.exists():
            self.documents = [Document(**item) for item in json.loads(self.path.read_text(encoding="utf-8"))]
            current_backend = self.embedder.backend
            for document in self.documents:
                stored_backend = (document.metadata or {}).get("embedding_backend")
                if not stored_backend or stored_backend != current_backend:
                    document.embedding = None

    def add_documents(self, documents: list[Document]) -> None:
        missing = [document.text for document in documents if document.embedding is None]
        vectors = iter(self.embedder.embed(missing))
        for document in documents:
            if document.embedding is None:
                document.embedding = next(vectors)
            document.metadata = document.metadata or {"embedding_model": self.embedder.metadata()["model"], "embedding_backend": self.embedder.backend}
        keys = {(document.file, document.section): document for document in self.documents}
        keys.update({(document.file, document.section): document for document in documents})
        self.documents = list(keys.values())
        self.path.write_text(json.dumps([asdict(item) for item in self.documents], indent=2), encoding="utf-8")

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        tokens = {token.lower() for token in query.split() if len(token) > 2}
        query_vector = self.embedder.embed([query])[0]
        ranked = []
        for document in self.documents:
            lexical = sum(token in document.text.lower() for token in tokens) / max(len(tokens), 1)
            semantic = cosine_similarity(query_vector, document.embedding or [])
            score = (0.55 * semantic) + (0.45 * lexical)
            if score > 0:
                item = asdict(document)
                item.pop("embedding", None)
                item["relevance"] = round(score, 4)
                item["distance"] = round(1 - score, 4)
                ranked.append((score, item))
        return [item for _score, item in sorted(ranked, key=lambda item: item[0], reverse=True)[:n_results]]

    def stats(self) -> dict:
        return {"doc_count": len({item.file for item in self.documents}), "chunk_count": len(self.documents), "size_bytes": self.path.stat().st_size if self.path.exists() else 0, "embedding": self.embedder.metadata(), "index_version": 2}


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    denominator = math.sqrt(sum(item * item for item in left)) * math.sqrt(sum(item * item for item in right))
    if denominator == 0:
        return 0.0
    return max(0.0, sum(a * b for a, b in zip(left, right)) / denominator)
