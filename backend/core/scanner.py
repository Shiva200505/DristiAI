import re
from backend.core.security.bandit_runner import run_bandit
from backend.core.security.findings_parser import FindingSchema
from backend.core.security.semgrep_runner import run_semgrep


PATTERNS = [
    ("DRISHTI-SQL-001", "critical", "SQL injection", r"(?:SELECT|INSERT|UPDATE|DELETE)[^\n]*(?:\+|\{|%\s|\.format\()", "CWE-89", "SQL query is built with interpolated input. Use a bound parameter."),
    ("DRISHTI-SHELL-006", "high", "Command injection", r"subprocess\.[^(]+\([^\n]*shell\s*=\s*True", "CWE-78", "Pass an argument list with shell=False and validate values."),
    ("DRISHTI-PATH-008", "high", "Path traversal", r"open\([^\n]*(?:user_input|request\.|filename)", "CWE-22", "Resolve and validate the path against an allowed base directory."),
    ("DRISHTI-SECRET-014", "high", "Hardcoded secret", r"(?:password|secret|api[_-]?key|token|AWS_SECRET_KEY)\s*=\s*[\"'][^\"']+[\"']", "CWE-798", "Load the secret from an environment-backed secret store."),
    ("DRISHTI-CRYPTO-018", "medium", "Weak cryptography", r"hashlib\.md5\(|hashlib\.sha1\(", "CWE-328", "Use a modern password hashing or cryptographic algorithm."),
    ("DRISHTI-DESER-019", "critical", "Insecure deserialization", r"pickle\.loads?\(", "CWE-502", "Use a safe, constrained serialization format."),
    ("DRISHTI-XSS-021", "medium", "Cross-site scripting", r"\.innerHTML\s*=|dangerouslySetInnerHTML", "CWE-79", "Render text through an escaping path or sanitize with an allowlist."),
    ("DRISHTI-SSRF-025", "high", "Server-side request forgery", r"(?:requests\.(?:get|post)|fetch)\([^\n]*(?:url|request\.)", "CWE-918", "Allowlist destinations and block private network ranges."),
]


def fallback_scan(code: str, filename: str, language: str = "python") -> list[FindingSchema]:
    findings = []
    for issue_id, severity, vuln_type, pattern, cwe, recommendation in PATTERNS:
        match = re.search(pattern, code, re.IGNORECASE)
        if not match:
            continue
        line = code[:match.start()].count("\n") + 1
        snippet = code.splitlines()[line - 1].strip() if code.splitlines() else match.group(0)
        findings.append(FindingSchema(issue_id=issue_id, severity=severity, confidence=0.97, issue_text=f"{vuln_type} detected by local deterministic rule", line_number=line, file_path=filename, vuln_type=vuln_type, code_snippet=snippet, cwe_id=cwe, test_id=issue_id, explanation=recommendation))
    return findings


def scan_code(code: str, filename: str, language: str = "python", use_external_tools: bool = True) -> list[FindingSchema]:
    findings = fallback_scan(code, filename, language)
    if use_external_tools:
        findings.extend(run_bandit(code, language, filename))
        findings.extend(run_semgrep(code, language, filename))
    unique = {}
    for finding in findings:
        unique[(finding.issue_id, finding.line_number)] = finding
    return list(unique.values())
