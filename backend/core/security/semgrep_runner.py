import json
import subprocess
import tempfile
from pathlib import Path
from backend.core.security.findings_parser import FindingSchema


def run_semgrep(code_snippet: str, language: str, filename: str, timeout: int = 30) -> list[FindingSchema]:
    extension = ".py" if language.lower() in {"python", "py"} else ".js"
    path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=extension, encoding="utf-8", delete=False) as handle:
            handle.write(code_snippet)
            path = Path(handle.name)
        result = subprocess.run(["semgrep", "--config", "auto", "--json", "--quiet", str(path)], capture_output=True, text=True, timeout=timeout)
        if not result.stdout.strip():
            return []
        findings = []
        for item in json.loads(result.stdout).get("results", []):
            extra = item.get("extra", {})
            metadata = extra.get("metadata") or {}
            cwe = metadata.get("cwe")
            if isinstance(cwe, list):
                cwe = cwe[0] if cwe else None
            findings.append(FindingSchema(issue_id=item.get("check_id", "SEMGREP"), severity=str(extra.get("severity", "WARNING")).lower(), confidence=float(metadata.get("confidence", 0.85)) if str(metadata.get("confidence", "")).replace(".", "", 1).isdigit() else 0.85, issue_text=extra.get("message", "Semgrep finding"), line_number=int(item.get("start", {}).get("line", 1)), file_path=filename, vuln_type=item.get("check_id", "Semgrep finding"), code_snippet=extra.get("lines", ""), cwe_id=str(cwe) if cwe else None, test_id=item.get("check_id"), source="semgrep", language=language.lower(), detector="Semgrep", column_number=int(item.get("start", {}).get("col", 1)), evidence={"metadata": metadata, "fingerprint": item.get("fingerprint")}))
        return findings
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError):
        return []
    finally:
        if path:
            path.unlink(missing_ok=True)
