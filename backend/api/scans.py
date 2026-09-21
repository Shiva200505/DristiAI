from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.api.schemas import DependencyScanRequest, ProjectScanRequest, ScanRequest
from backend.config import settings
from backend.core.scanner import scan_code, scan_project
from backend.core.security.dependency_scanner import scan_dependencies
from backend.database.crud import get_or_create_project, record_scan
from backend.database.session import get_db
from backend.utils.hardware import hardware_payload

router = APIRouter(prefix="/api/scans", tags=["scans"])


def finding_payload(item):
    return item.as_dict() if hasattr(item, "as_dict") else item


@router.post("/trigger")
@router.post("")
def trigger_scan(payload: ScanRequest, db: Session = Depends(get_db)):
    started = datetime.now(timezone.utc)
    findings = scan_code(payload.code_content, payload.file_path, payload.language)
    project = get_or_create_project(db, "VS Code workspace", str(settings.root / "workspace"), payload.language)
    scan = record_scan(db, payload.file_path, payload.triggered_by, [finding_payload(item) for item in findings], project)
    return {"scan_id": scan.id, "status": "complete", "started_at": started, "completed_at": datetime.now(timezone.utc), "findings": [finding_payload(item) for item in findings], "backend": hardware_payload()}


@router.post("/project")
def trigger_project_scan(payload: ProjectScanRequest, db: Session = Depends(get_db)):
    result = scan_project(payload.project_root, payload.changed_files or None, payload.use_external_tools)
    if result["scanned_files"]:
        project = get_or_create_project(db, Path(payload.project_root).name or "Workspace", str(Path(payload.project_root).resolve()), "mixed")
        persisted = record_scan(db, payload.project_root, payload.triggered_by, result["findings"], project)
        result["scan_id"] = persisted.id
    return {**result, "status": "complete", "backend": hardware_payload(), "triggered_by": payload.triggered_by}


@router.post("/dependencies")
def trigger_dependency_scan(payload: DependencyScanRequest):
    return scan_dependencies(payload.project_root, payload.allow_network).as_dict()
