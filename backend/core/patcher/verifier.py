from dataclasses import asdict, dataclass
from backend.core.scanner import scan_code
from backend.core.security.findings_parser import FindingSchema


@dataclass
class VerificationResult:
    status: str
    pre_scan_findings: list[dict]
    post_scan_findings: list[dict]
    resolved_count: int
    new_findings: list[dict]
    message: str

    def as_dict(self):
        return asdict(self)


def verify_patch(finding: FindingSchema, original_code: str, patched_code: str, language: str = "python") -> VerificationResult:
    before = scan_code(original_code, finding.file_path, language, use_external_tools=False)
    after = scan_code(patched_code, finding.file_path, language, use_external_tools=False)
    remaining = [item for item in after if item.issue_id == finding.issue_id]
    before_ids = {item.issue_id for item in before}
    new_findings = [item for item in after if item.issue_id not in before_ids]
    status = "STILL_VULNERABLE" if remaining else "RESOLVED"
    return VerificationResult(status, [item.as_dict() for item in before], [item.as_dict() for item in after], 0 if remaining else 1, [item.as_dict() for item in new_findings], "The original rule is no longer matched." if not remaining else "The original finding still matches the patched code.")
