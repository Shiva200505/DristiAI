from fastapi import APIRouter
from pydantic import BaseModel, Field
from backend.core.retrieval.indexer import index_path
from backend.core.retrieval.retriever import retrieve
from backend.core.retrieval.vector_store import LocalVectorStore

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class IndexRequest(BaseModel):
    project_root: str
    project_slug: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    project_slug: str = "default"
    n_results: int = Field(default=5, ge=1, le=20)


@router.post("/index")
def index_project(payload: IndexRequest):
    return {"indexed_chunks": index_path(payload.project_root, LocalVectorStore(payload.project_slug or "default"))}


@router.post("/search")
def search_knowledge(payload: SearchRequest):
    return {"items": retrieve(payload.query, payload.project_slug, payload.n_results)}


@router.get("/stats/{project_slug}")
def knowledge_stats(project_slug: str):
    return LocalVectorStore(project_slug).stats()
