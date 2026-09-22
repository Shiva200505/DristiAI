import re
import shutil
import time
from pathlib import Path
from backend.core.security.bandit_runner import run_bandit
from backend.core.security.ast_analysis import analyze_python, ast_capabilities
from backend.core.security.findings_parser import FindingSchema
from backend.core.security.semgrep_runner import run_semgrep


PATTERNS = [
    ("DRISHTI-SQL-001", "critical", "SQL injection", r"\b(?:SELECT|INSERT|UPDATE|DELETE)\s+[^\n]*(?:\+|\{|%\s|\.format\()", "CWE-89", "SQL query is built with interpolated input. Use a bound parameter."),
    ("DRISHTI-SHELL-006", "high", "Command injection", r"subprocess\.[^(]+\([^\n]*shell\s*=\s*True", "CWE-78", "Pass an argument list with shell=False and validate values."),
    ("DRISHTI-PATH-008", "high", "Path traversal", r"open\([^\n]*(?:user_input|request\.|filename)", "CWE-22", "Resolve and validate the path against an allowed base directory."),
    ("DRISHTI-SECRET-014", "high", "Hardcoded secret", r"(?:password|secret|api[_-]?key|token|AWS_SECRET_KEY)\s*=\s*[\"'][^\"']+[\"']", "CWE-798", "Load the secret from an environment-backed secret store."),
    ("DRISHTI-CRYPTO-018", "medium", "Weak cryptography", r"hashlib\.md5\(|hashlib\.sha1\(", "CWE-328", "Use a modern password hashing or cryptographic algorithm."),
    ("DRISHTI-DESER-019", "critical", "Insecure deserialization", r"pickle\.loads?\(", "CWE-502", "Use a safe, constrained serialization format."),
    ("DRISHTI-XSS-021", "medium", "Cross-site scripting", r"\.innerHTML\s*=|dangerouslySetInnerHTML", "CWE-79", "Render text through an escaping path or sanitize with an allowlist."),
    ("DRISHTI-SSRF-025", "high", "Server-side request forgery", r"(?:requests\.(?:get|post)|fetch)\([^\n]*(?:url|request\.)", "CWE-918", "Allowlist destinations and block private network ranges."),
    ("DRISHTI-YAML-026", "high", "Unsafe YAML loading", r"yaml\.load\((?![^\n]*SafeLoader)", "CWE-502", "Use yaml.safe_load or an explicit SafeLoader for untrusted YAML."),
    ("DRISHTI-EVAL-022", "critical", "Dynamic code execution", r"\b(?:eval|exec)\s*\(", "CWE-95", "Avoid dynamic code execution and use a constrained parser or allowlist."),
    ("DRISHTI-TLS-030", "high", "TLS certificate verification disabled", r"(?:requests|httpx)\.[^(]+\([^\n]*verify\s*=\s*False", "CWE-295", "Keep TLS certificate verification enabled."),
    ("DRISHTI-TEMP-031", "high", "Insecure temporary file", r"tempfile\.mktemp\(", "CWE-377", "Use NamedTemporaryFile or mkstemp for atomic temporary-file creation."),
    ("DRISHTI-JWT-029", "high", "JWT signature verification disabled", r"verify_signature\s*[:=]\s*False", "CWE-347", "Require JWT signature verification and an algorithm allowlist."),
]


def fallback_scan(code: str, filename: str, language: str = "python") -> list[FindingSchema]:
    findings = []
    normalized_language = language.lower()
    source_lines = code.splitlines()
    for issue_id, severity, vuln_type, pattern, cwe, recommendation in PATTERNS:
        for match in re.finditer(pattern, code, re.IGNORECASE):
            line = code[:match.start()].count("\n") + 1
            column = match.start() - (code.rfind("\n", 0, match.start()) + 1) + 1
            snippet = source_lines[line - 1].strip() if source_lines and line <= len(source_lines) else match.group(0)
            start = max(0, line - 3)
            end = min(len(source_lines), line + 2)
            context = "\n".join(source_lines[start:end])
            findings.append(FindingSchema(
                issue_id=issue_id,
                severity=severity,
                confidence=0.97,
                issue_text=f"{vuln_type} detected by local deterministic rule",
                line_number=line,
                file_path=filename,
                vuln_type=vuln_type,
                code_snippet=snippet,
                cwe_id=cwe,
                test_id=issue_id,
                source="deterministic",
                language=normalized_language,
                detector="Drishti deterministic rules",
                column_number=column,
                surrounding_context=context,
                evidence={"matched_rule": issue_id, "match": mask_for_evidence(match.group(0))},
                attack_scenario=f"An attacker-controlled value reaches the {vuln_type.lower()} sink at {filename}:{line}.",
                explanation=recommendation,
                recommendation=recommendation,
            ))
    return findings


def mask_for_evidence(value: str) -> str:
    from backend.core.security.findings_parser import mask_secrets
    return mask_secrets(value)


def scan_code(code: str, filename: str, language: str = "python", use_external_tools: bool = True) -> list[FindingSchema]:
    findings = fallback_scan(code, filename, language)
    if language.lower() in {"python", "py"}:
        findings.extend(analyze_python(code, filename))
    if use_external_tools:
        findings.extend(run_bandit(code, language, filename))
        findings.extend(run_semgrep(code, language, filename))
    unique = {}
    for finding in findings:
        finding.language = finding.language if finding.language != "unknown" else language.lower()
        key = (finding.file_path, finding.line_number, finding.cwe_id or finding.vuln_type.lower())
        current = unique.get(key)
        if current is None or source_priority(finding.source) > source_priority(current.source):
            unique[key] = finding
    return sorted(unique.values(), key=lambda item: (item.line_number, item.severity, item.issue_id))


def source_priority(source: str) -> int:
    return {"semgrep": 4, "bandit": 3, "ast": 2, "deterministic": 1, "osv-scanner": 4}.get(source, 0)


def scanner_capabilities(use_external_tools: bool = True) -> dict:
    tools = {
        "deterministic": {"installed": True, "executed": True, "status": "available", "findings": None},
        "ast": ast_capabilities(),
        "bandit": {"installed": shutil.which("bandit") is not None, "executed": bool(use_external_tools and shutil.which("bandit")), "status": "available" if shutil.which("bandit") else "optional_unavailable", "findings": None},
        "semgrep": {"installed": shutil.which("semgrep") is not None, "executed": bool(use_external_tools and shutil.which("semgrep")), "status": "available" if shutil.which("semgrep") else "optional_unavailable", "findings": None},
    }
    return tools


def scan_code_with_report(code: str, filename: str, language: str = "python", use_external_tools: bool = True) -> tuple[list[FindingSchema], dict]:
    started = time.perf_counter()
    findings = scan_code(code, filename, language, use_external_tools)
    report = scanner_capabilities(use_external_tools)
    report["deterministic"]["findings"] = sum(item.source == "deterministic" for item in findings)
    report["ast"]["findings"] = sum(item.source == "ast" for item in findings)
    report["bandit"]["findings"] = sum(item.source == "bandit" for item in findings)
    report["semgrep"]["findings"] = sum(item.source == "semgrep" for item in findings)
    report["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return findings, report


def scan_file(path: str | Path, root: str | Path | None = None, use_external_tools: bool = True) -> list[FindingSchema]:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    display_path = str(file_path.relative_to(root)) if root and file_path.is_relative_to(Path(root)) else str(file_path)
    language = {".py": "python", ".js": "javascript", ".jsx": "javascript", ".ts": "typescript", ".tsx": "typescript"}.get(file_path.suffix.lower(), file_path.suffix.lstrip(".") or "unknown")
    return scan_code(text, display_path, language, use_external_tools=use_external_tools)


def scan_project(root: str | Path, changed_files: list[str] | None = None, use_external_tools: bool = True) -> dict:
    project_root = Path(root).resolve()
    if not project_root.is_dir():
        return {"root": str(project_root), "scanned_files": 0, "changed_files": bool(changed_files), "findings": [], "errors": [{"file": str(project_root), "error": "Project directory does not exist."}]}
    allowed = {".py", ".js", ".jsx", ".ts", ".tsx"}
    excluded = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".drishti"}
    candidates = []
    if changed_files:
        candidates = [project_root / item for item in changed_files]
    else:
        candidates = [item for item in project_root.rglob("*") if item.is_file() and item.suffix.lower() in allowed and not excluded.intersection(item.parts)]
    findings = []
    scanned_files = 0
    errors = []
    for file_path in candidates:
        try:
            if file_path.is_file() and file_path.suffix.lower() in allowed and not excluded.intersection(file_path.parts):
                findings.extend(scan_file(file_path, project_root, use_external_tools))
                scanned_files += 1
        except (OSError, UnicodeDecodeError) as exc:
            errors.append({"file": str(file_path), "error": str(exc)})
    return {"root": str(project_root), "scanned_files": scanned_files, "changed_files": bool(changed_files), "findings": [item.as_dict() for item in findings], "errors": errors, "scanner_capabilities": scanner_capabilities(use_external_tools)}
