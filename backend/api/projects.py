from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.crud import get_or_create_project
from backend.database.session import get_db
from backend.api.schemas import ProjectCreate
from backend.utils.paths import resolve_approved_workspace

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("")
def register_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    try:
        project_path = resolve_approved_workspace(payload.path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "PROJECT_PATH_NOT_APPROVED", "message": str(exc)}) from exc
    project = get_or_create_project(db, payload.name, str(project_path), payload.language)
    return {"id": project.id, "name": project.name, "path": project.path, "language": project.language}


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    from backend.database.models import Project
    return {"items": [{"id": item.id, "name": item.name, "path": item.path, "language": item.language, "last_scanned": item.last_scanned} for item in db.query(Project).order_by(Project.id.desc()).all()]}
