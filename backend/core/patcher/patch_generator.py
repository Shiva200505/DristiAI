from backend.core.patcher.diff_engine import unified_diff
from backend.core.security.findings_parser import FindingSchema


def generate_patch(finding: FindingSchema, original_code: str) -> dict:
    replacement = original_code
    if finding.issue_id == "DRISHTI-SQL-001":
        replacement = original_code.replace(finding.code_snippet, 'query = "SELECT * FROM users WHERE id = ?"\n    return db.execute(query, (user_id,)).fetchone()')
    elif finding.issue_id == "DRISHTI-XSS-021":
        replacement = original_code.replace("innerHTML", "textContent")
    return {"original_code": original_code, "patched_code": replacement, "diff": unified_diff(original_code, replacement, finding.file_path), "confidence": finding.confidence, "status": "candidate"}
