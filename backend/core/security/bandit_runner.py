import json
import subprocess
import sys
import tempfile
from pathlib import Path
from backend.core.security.findings_parser import FindingSchema


def run_bandit(code_snippet: str, language: str, filename: str, timeout: int = 30) -> list[FindingSchema]:
    if language.lower() not in {"python", "py"}:
        return []
    path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8", delete=False) as handle:
            handle.write(code_snippet)
            path = Path(handle.name)
        result = subprocess.run([sys.executable, "-m", "bandit", "-f", "json", "-q", str(path)], capture_output=True, text=True, timeout=timeout)
        if not result.stdout.strip():
            return []
        payload = json.loads(result.stdout)
        findings = []
        for item in payload.get("results", []):
            cwe = item.get("issue_cwe") or {}
            findings.append(FindingSchema(issue_id=item.get("test_id", "BANDIT"), severity=item.get("issue_severity", "MEDIUM").lower(), confidence=float(item.get("issue_confidence", "MEDIUM") == "HIGH" or 0.7), issue_text=item.get("issue_text", "Bandit finding"), line_number=int(item.get("line_number", 1)), file_path=filename, vuln_type=item.get("test_name", "Bandit finding"), code_snippet=item.get("code", ""), cwe_id=str(cwe.get("id")) if cwe.get("id") else None, test_id=item.get("test_id"), source="bandit"))
        return findings
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError):
        return []
    finally:
        if path:
            path.unlink(missing_ok=True)
