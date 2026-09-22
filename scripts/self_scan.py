"""Run Drishti's canonical deterministic scanner against this repository."""

from __future__ import annotations

from datetime import datetime, timezone
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.core.scanner import scan_project


def scope_for(path: str) -> str:
    normalized = path.replace('\\', '/').lower()
    if normalized.startswith(('demo-repo/', 'tests/', 'workspace/', 'benchmarks/')):
        return 'intentional fixture/test surface'
    if normalized in {'backend/core/scanner.py', 'backend/core/security/ast_analysis.py'}:
        return 'scanner implementation self-match'
    return 'application surface requiring review'


def main() -> int:
    result = scan_project(ROOT, use_external_tools=False)
    findings = result["findings"]
    counts = Counter(scope_for(item["file_path"]) for item in findings)
    report = [
        "# Drishti self-scan report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "This report is an actual deterministic scan of the repository using `backend.core.scanner`. Optional Semgrep/Bandit/OSV results are not included in this run.",
        "",
        f"- Scanned files: {result['scanned_files']}",
        f"- Findings: {len(findings)}",
        f"- Errors: {len(result['errors'])}",
        "- External tools: disabled for reproducible local self-scan",
        "",
        "## Scope summary",
        "",
        "The scope labels are review aids, not suppressions. Every finding remains listed below.",
        "",
    ]
    report.extend(f"- {scope}: {counts.get(scope, 0)}" for scope in ('application surface requiring review', 'scanner implementation self-match', 'intentional fixture/test surface'))
    report.extend(["", "## Application surface requiring review", ""])
    application_findings = [item for item in findings if scope_for(item['file_path']) == 'application surface requiring review']
    if application_findings:
        report.extend(f"- **{item['severity'].upper()}** `{item['issue_id']}` - `{item['file_path']}:{item['line_number']}` - {item['issue_text']}" for item in application_findings)
    else:
        report.append("No findings outside the intentional fixture/test and scanner implementation scopes.")
    report.extend(["", "## Scanner implementation self-matches", ""])
    scanner_findings = [item for item in findings if scope_for(item['file_path']) == 'scanner implementation self-match']
    if scanner_findings:
        report.extend(f"- `{item['issue_id']}` - `{item['file_path']}:{item['line_number']}` - rule-pattern self-match; review only if the analyzer implementation changes." for item in scanner_findings)
    else:
        report.append("None.")
    report.extend(["", "## Intentional fixture/test surface", ""])
    fixture_findings = [item for item in findings if scope_for(item['file_path']) == 'intentional fixture/test surface']
    if fixture_findings:
        report.extend(f"- `{item['issue_id']}` - `{item['file_path']}:{item['line_number']}` - intentional vulnerable sample or scanner test fixture." for item in fixture_findings)
    else:
        report.append("None.")
    report.extend(["", "## Full deterministic output", ""])
    if not findings:
        report.append("No deterministic findings were returned by the current rule set.")
    else:
        report.extend(f"- **{item['severity'].upper()}** `{item['issue_id']}` - `{item['file_path']}:{item['line_number']}` - {item['issue_text']}" for item in findings)
    if result["errors"]:
        report.extend(["", "## Scan errors", ""])
        report.extend(f"- `{item['file']}` - {item['error']}" for item in result["errors"])
    target = ROOT / "docs" / "self-scan-report.md"
    target.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Scanned {result['scanned_files']} files and wrote {len(findings)} findings to {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
