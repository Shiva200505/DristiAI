from dataclasses import asdict, dataclass
import ast
import difflib
import subprocess
from backend.core.scanner import scan_code
from backend.core.security.findings_parser import FindingSchema
from backend.core.patcher.patch_generator import MAX_CHANGED_LINES, MAX_PATCH_LINES


@dataclass
class VerificationResult:
    status: str
    pre_scan_findings: list[dict]
    post_scan_findings: list[dict]
    resolved_count: int
    new_findings: list[dict]
    message: str
    verification_status: str = "REQUIRES_MANUAL_REVIEW"
    checks: list[dict] | None = None

    def as_dict(self):
        return asdict(self)


def verify_patch(finding: FindingSchema, original_code: str, patched_code: str, language: str = "python") -> VerificationResult:
    before = scan_code(original_code, finding.file_path, language, use_external_tools=False)
    after = scan_code(patched_code, finding.file_path, language, use_external_tools=False)
    remaining = [item for item in after if item.issue_id == finding.issue_id]
    before_ids = {item.issue_id for item in before}
    new_findings = [item for item in after if item.issue_id not in before_ids]
    diff = "".join(difflib.unified_diff(original_code.splitlines(True), patched_code.splitlines(True)))
    diff_lines = len(diff.splitlines())
    changed_lines = sum(1 for line in diff.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
    checks = [{"name": "security_rule", "status": "FAIL" if remaining else "PASS", "detail": "Original finding is still detected." if remaining else "Original finding is no longer detected."}]
    checks.append({"name": "bounded_diff", "status": "PASS" if diff_lines <= MAX_PATCH_LINES and changed_lines <= MAX_CHANGED_LINES else "FAIL", "detail": f"{changed_lines} changed line(s), {diff_lines} diff line(s)."})
    syntax = syntax_check(patched_code, language)
    checks.append(syntax)
    checks.append({"name": "new_findings", "status": "FAIL" if new_findings else "PASS", "detail": f"{len(new_findings)} new deterministic finding(s) detected." if new_findings else "No new deterministic findings detected."})
    if remaining:
        verification_status = "STILL_VULNERABLE"
    elif checks[1]["status"] == "FAIL":
        verification_status = "PATCH_TOO_LARGE"
    elif syntax["status"] == "FAIL":
        verification_status = "PATCH_INVALID"
    elif new_findings:
        verification_status = "NEW_FINDINGS_INTRODUCED"
    else:
        verification_status = "VERIFIED_RESOLVED"
    legacy_status = "STILL_VULNERABLE" if verification_status != "VERIFIED_RESOLVED" else "RESOLVED"
    return VerificationResult(legacy_status, [item.as_dict() for item in before], [item.as_dict() for item in after], 0 if remaining else 1, [item.as_dict() for item in new_findings], "The original rule is no longer matched." if not remaining else "The original finding still matches the patched code.", verification_status, checks)


def syntax_check(code: str, language: str) -> dict:
    normalized = language.lower()
    try:
        if normalized in {"python", "py"}:
            ast.parse(code)
            return {"name": "syntax", "status": "PASS", "detail": "Python AST parsed successfully."}
        if normalized in {"javascript", "typescript", "js", "ts"}:
            result = subprocess.run(["node", "--check"], input=code, capture_output=True, text=True, timeout=5, check=False)
            return {"name": "syntax", "status": "PASS" if result.returncode == 0 else "FAIL", "detail": "Node syntax check passed." if result.returncode == 0 else "Node syntax check failed."}
        return {"name": "syntax", "status": "NOT_RUN", "detail": f"No syntax checker configured for {language}."}
    except (SyntaxError, FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return {"name": "syntax", "status": "FAIL", "detail": f"Syntax validation failed: {type(exc).__name__}."}
