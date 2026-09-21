from fastapi import APIRouter
from backend.api.schemas import ChatRequest
from backend.core.retrieval.retriever import retrieve

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
def ask_drishti(payload: ChatRequest):
    matches = retrieve(payload.message, payload.project_slug)
    if matches:
        answer = matches[0]["text"][:600]
        source = matches[0]["file"]
    else:
        answer = "No matching local project context was found. Index project documents first, or ask about an active security finding."
        source = "local-index"
    return {"answer": answer, "source": source, "network": "none", "model": "local retrieval fallback"}
