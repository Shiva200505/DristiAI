from dataclasses import asdict, dataclass


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

    def as_dict(self) -> dict:
        return asdict(self)
