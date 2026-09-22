from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.api.schemas import DependencyScanRequest, ProjectScanRequest, ScanRequest
from backend.api.findings import finding_payload as database_finding_payload
from backend.config import settings
from backend.core.scanner import scan_code_with_report, scan_project
from backend.core.security.dependency_scanner import scan_dependencies
from backend.database.crud import get_or_create_project, record_scan
from backend.database.session import get_db
from backend.utils.hardware import hardware_payload
from backend.utils.paths import resolve_approved_workspace

router = APIRouter(prefix="/api/scans", tags=["scans"])


def finding_payload(item):
    return item.as_dict() if hasattr(item, "as_dict") else item


@router.post("/trigger")
@router.post("")
def trigger_scan(payload: ScanRequest, db: Session = Depends(get_db)):
    started = datetime.now(timezone.utc)
    findings, scanner_report = scan_code_with_report(payload.code_content, payload.file_path, payload.language)
    if payload.project_root:
        try:
            project_root = resolve_approved_workspace(payload.project_root)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={"code": "PROJECT_PATH_NOT_APPROVED", "message": str(exc)}) from exc
    else:
        project_root = settings.root / "workspace"
    project = get_or_create_project(db, project_root.name or "Workspace", str(project_root), payload.language)
    scan = record_scan(db, payload.file_path, payload.triggered_by, [finding_payload(item) for item in findings], project)
    persisted_findings = [database_finding_payload(item) for item in scan.findings]
    return {"scan_id": scan.id, "status": "complete", "started_at": started, "completed_at": datetime.now(timezone.utc), "findings": persisted_findings, "backend": hardware_payload(), "scanner_report": scanner_report}


@router.post("/project")
def trigger_project_scan(payload: ProjectScanRequest, db: Session = Depends(get_db)):
    try:
        project_root = resolve_approved_workspace(payload.project_root)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail={"code": "PROJECT_PATH_NOT_APPROVED", "message": str(exc)}) from exc
    result = scan_project(project_root, payload.changed_files or None, payload.use_external_tools)
    if result["scanned_files"]:
        project = get_or_create_project(db, project_root.name or "Workspace", str(project_root), "mixed")
        persisted = record_scan(db, str(project_root), payload.triggered_by, result["findings"], project)
        result["scan_id"] = persisted.id
    return {**result, "status": "complete", "backend": hardware_payload(), "triggered_by": payload.triggered_by}


@router.post("/dependencies")
def trigger_dependency_scan(payload: DependencyScanRequest):
    try:
        project_root = resolve_approved_workspace(payload.project_root)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail={"code": "PROJECT_PATH_NOT_APPROVED", "message": str(exc)}) from exc
    return scan_dependencies(project_root, payload.allow_network).as_dict()
