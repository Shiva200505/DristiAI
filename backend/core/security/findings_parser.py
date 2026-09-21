from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
import hashlib
import re


FINDING_STATUSES = {
    "RULE_DETECTED",
    "AI_INFERRED",
    "AI_EXPLAINED",
    "PATCH_PROPOSED",
    "PATCH_APPLIED",
    "PATCH_VERIFIED",
    "REQUIRES_REVIEW",
}

OWASP_BY_CWE = {
    "CWE-22": "A01:2021 Broken Access Control",
    "CWE-78": "A03:2021 Injection",
    "CWE-79": "A03:2021 Injection",
    "CWE-89": "A03:2021 Injection",
    "CWE-218": "A07:2021 Identification and Authentication Failures",
    "CWE-328": "A02:2021 Cryptographic Failures",
    "CWE-502": "A08:2021 Software and Data Integrity Failures",
    "CWE-798": "A07:2021 Identification and Authentication Failures",
    "CWE-918": "A10:2021 Server-Side Request Forgery",
}


def mask_secrets(value: str) -> str:
    """Keep evidence useful without persisting credential-like literals."""
    if not value:
        return value
    patterns = (
        r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+",
        r"(?i)(password|secret|token|api[_-]?key|aws_secret_access_key)\s*([=:])\s*(['\"])[^'\"]+\3",
        r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----",
        r"(?i)(AKIA[0-9A-Z]{12,})",
    )
    masked = value
    for pattern in patterns:
        if pattern.startswith("(?i)(bearer"):
            masked = re.sub(pattern, r"\1[REDACTED]", masked)
        elif "PRIVATE KEY" in pattern:
            masked = re.sub(pattern, "[REDACTED PRIVATE KEY]", masked)
        elif "AKIA" in pattern:
            masked = re.sub(pattern, "[REDACTED ACCESS KEY]", masked)
        else:
            masked = re.sub(pattern, lambda match: f"{match.group(1)}{match.group(2)}{match.group(3)}[REDACTED]{match.group(3)}", masked)
    return masked


@dataclass
class FindingSchema:
    issue_id: str
    severity: str
    confidence: float
    issue_text: str
    line_number: int
    file_path: str
    vuln_type: str
    code_snippet: str
    cwe_id: str | None = None
    test_id: str | None = None
    source: str = "deterministic"
    explanation: str = ""
    rule_id: str | None = None
    vulnerability_type: str | None = None
    owasp_category: str | None = None
    column_number: int | None = None
    language: str = "unknown"
    detector: str = "Drishti deterministic rules"
    surrounding_context: str = ""
    evidence: dict = field(default_factory=dict)
    attack_scenario: str = ""
    recommendation: str = ""
    candidate_patch: str = ""
    patch_status: str = "NOT_PROPOSED"
    verification_status: str = "NOT_RUN"
    verification_results: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        self.rule_id = self.rule_id or self.issue_id
        self.vulnerability_type = self.vulnerability_type or self.vuln_type
        self.owasp_category = self.owasp_category or OWASP_BY_CWE.get(self.cwe_id or "")
        self.recommendation = self.recommendation or self.explanation
        self.code_snippet = mask_secrets(self.code_snippet)
        self.surrounding_context = mask_secrets(self.surrounding_context)
        if self.source in {"deterministic", "bandit", "semgrep"} and self.patch_status == "NOT_PROPOSED":
            self.patch_status = "RULE_DETECTED"
        if not self.evidence:
            self.evidence = {"detector": self.detector, "rule_id": self.rule_id}

    @property
    def fingerprint(self) -> str:
        value = f"{self.file_path}:{self.line_number}:{self.rule_id}:{self.code_snippet}"
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload["id"] = self.fingerprint
        payload["status"] = self.patch_status
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> "FindingSchema":
        allowed = {item.name for item in fields(cls)}
        return cls(**{key: value for key, value in payload.items() if key in allowed})
