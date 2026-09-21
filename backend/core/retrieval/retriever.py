from backend.core.retrieval.vector_store import LocalVectorStore


def retrieve(query: str, project_slug: str = "default", n_results: int = 5) -> list[dict]:
    return LocalVectorStore(project_slug).search(query, n_results)
