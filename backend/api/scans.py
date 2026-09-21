from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.api.schemas import ScanRequest
from backend.config import settings
from backend.core.scanner import scan_code
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
