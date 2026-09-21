import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database.session import init_db
from backend.api import chat, findings, knowledge, patches, projects, runtime, scans, system

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    logging.info("Drishti backend started; local_only=%s", settings.local_only)
    yield


app = FastAPI(title="Drishti AI Local Security API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.cors_origin, "http://localhost:4173", "http://127.0.0.1:4173"], allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])


@app.middleware("http")
async def request_logging(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    logging.info("%s %s -> %s in %.1fms", request.method, request.url.path, response.status_code, (time.perf_counter() - started) * 1000)
    return response


app.include_router(projects.router)
app.include_router(scans.router)
app.include_router(findings.router)
app.include_router(patches.router)
app.include_router(chat.router)
app.include_router(system.router)
app.include_router(knowledge.router)
app.include_router(runtime.router)


@app.get("/health")
def health():
    return {"ok": True, "service": "drishti-backend", "local_only": settings.local_only}
