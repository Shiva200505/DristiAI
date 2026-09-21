from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.crud import get_or_create_project
from backend.database.session import get_db
from backend.api.schemas import ProjectCreate

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("")
def register_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project_path = Path(payload.path).expanduser().resolve()
    if not project_path.is_dir():
        raise HTTPException(status_code=400, detail={"code": "PROJECT_NOT_FOUND", "message": "Project path must be an existing local directory."})
    project = get_or_create_project(db, payload.name, str(project_path), payload.language)
    return {"id": project.id, "name": project.name, "path": project.path, "language": project.language}


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    from backend.database.models import Project
    return {"items": [{"id": item.id, "name": item.name, "path": item.path, "language": item.language, "last_scanned": item.last_scanned} for item in db.query(Project).order_by(Project.id.desc()).all()]}
