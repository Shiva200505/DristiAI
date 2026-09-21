from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.models import Finding
from backend.database.session import get_db

router = APIRouter(prefix="/api/findings", tags=["findings"])


@router.get("")
def list_findings(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Finding).order_by(Finding.id.desc())
    if status:
        query = query.filter(Finding.status == status.upper())
    return {"items": [{"id": item.id, "issue_id": item.issue_id, "severity": item.severity, "vuln_type": item.vuln_type, "line_number": item.line_number, "file_path": item.file_path, "status": item.status, "confidence": item.confidence, "source": "deterministic"} for item in query.limit(100).all()]}


@router.get("/{finding_id}")
def get_finding(finding_id: int, db: Session = Depends(get_db)):
    item = db.get(Finding, finding_id)
    if not item:
        raise HTTPException(404, "Finding not found")
    return {"id": item.id, "issue_id": item.issue_id, "severity": item.severity, "vuln_type": item.vuln_type, "line_number": item.line_number, "file_path": item.file_path, "code_snippet": item.code_snippet, "cwe_id": item.cwe_id, "explanation": item.explanation, "status": item.status, "confidence": item.confidence}
