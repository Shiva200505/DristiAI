from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.database.models import Finding, Project, Scan


def get_or_create_project(db: Session, name: str, path: str, language: str = "Python") -> Project:
    project = db.query(Project).filter(Project.path == path).first()
    if project:
        return project
    project = Project(name=name, path=path, language=language)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def record_scan(db: Session, file_path: str, triggered_by: str, findings: list[dict], project: Project | None = None) -> Scan:
    scan = Scan(project_id=project.id if project else None, file_scanned=file_path, triggered_by=triggered_by, status="complete", completed_at=datetime.now(timezone.utc), findings_count=len(findings))
    db.add(scan)
    db.flush()
    for item in findings:
        db.add(Finding(scan_id=scan.id, issue_id=item["issue_id"], severity=item["severity"], vuln_type=item["vuln_type"], line_number=item["line_number"], file_path=item["file_path"], code_snippet=item["code_snippet"], cwe_id=item.get("cwe_id"), explanation=item.get("explanation", ""), confidence=item.get("confidence", 0.8)))
    db.commit()
    db.refresh(scan)
    return scan
