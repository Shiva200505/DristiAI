import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.models import Finding
from backend.database.session import get_db
from backend.api.schemas import ExplainRequest
from backend.core.ai.explainer import ExplainerService
from backend.core.security.findings_parser import FindingSchema

router = APIRouter(prefix="/api/findings", tags=["findings"])


@router.get("")
def list_findings(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Finding).order_by(Finding.id.desc())
    if status:
        query = query.filter(Finding.status == status.upper())
    return {"items": [finding_payload(item) for item in query.limit(100).all()]}


@router.get("/{finding_id}")
def get_finding(finding_id: int, db: Session = Depends(get_db)):
    item = db.get(Finding, finding_id)
    if not item:
        raise HTTPException(404, "Finding not found")
    return finding_payload(item)


@router.post("/{finding_id}/explain")
def explain_finding(finding_id: int, payload: ExplainRequest, db: Session = Depends(get_db)):
    item = db.get(Finding, finding_id)
    if not item:
        raise HTTPException(404, "Finding not found")
    finding = FindingSchema(issue_id=item.issue_id, severity=item.severity, confidence=item.confidence, issue_text=item.explanation or item.vuln_type, line_number=item.line_number, file_path=item.file_path, vuln_type=item.vuln_type, code_snippet=item.code_snippet, cwe_id=item.cwe_id, source=item.source or "deterministic", rule_id=item.rule_id, owasp_category=item.owasp_category, column_number=item.column_number, language=item.language or "unknown", detector=item.detector or "unknown", attack_scenario=item.attack_scenario or "", recommendation=item.recommendation or item.explanation or "")
    return ExplainerService().explain_finding(finding, payload.code_context, payload.rag_context).as_dict()


def finding_payload(item: Finding) -> dict:
    return {
        "id": item.id,
        "issue_id": item.issue_id,
        "rule_id": item.rule_id or item.issue_id,
        "severity": item.severity,
        "vuln_type": item.vuln_type,
        "vulnerability_type": item.vuln_type,
        "line_number": item.line_number,
        "column_number": item.column_number,
        "file_path": item.file_path,
        "language": item.language,
        "source": item.source or "deterministic",
        "detector": item.detector,
        "code_snippet": item.code_snippet,
        "cwe_id": item.cwe_id,
        "owasp_category": item.owasp_category,
        "evidence": json.loads(item.evidence or "{}"),
        "attack_scenario": item.attack_scenario,
        "explanation": item.explanation,
        "recommendation": item.recommendation or item.explanation,
        "status": item.status,
        "patch_status": item.patch_status,
        "verification_status": item.verification_status,
        "verification_results": json.loads(item.verification_results or "{}"),
        "confidence": item.confidence,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }
