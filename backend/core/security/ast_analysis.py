"""Small, dependency-free AST analysis for Python security sinks.

The regex baseline remains useful for fast coverage and non-Python files. This
module adds structure-aware checks for Python so calls, keyword values, and
assignment targets are not inferred from raw text alone.
"""

from __future__ import annotations

import ast
import importlib.util

from backend.core.security.findings_parser import FindingSchema


def _name(node: ast.AST | None) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _source_context(code: str, line: int) -> tuple[str, str]:
    lines = code.splitlines()
    snippet = lines[line - 1].strip() if 0 < line <= len(lines) else ""
    start = max(0, line - 3)
    end = min(len(lines), line + 2)
    return snippet, "\n".join(lines[start:end])


def _finding(code: str, filename: str, node: ast.AST, issue_id: str, severity: str, vuln_type: str, cwe: str, recommendation: str, issue_text: str | None = None) -> FindingSchema:
    line = int(getattr(node, "lineno", 1))
    column = int(getattr(node, "col_offset", 0)) + 1
    snippet, context = _source_context(code, line)
    return FindingSchema(
        issue_id=issue_id,
        severity=severity,
        confidence=0.94,
        issue_text=issue_text or f"{vuln_type} detected by Python AST analysis",
        line_number=line,
        column_number=column,
        file_path=filename,
        vuln_type=vuln_type,
        code_snippet=snippet,
        cwe_id=cwe,
        test_id=issue_id,
        source="ast",
        language="python",
        detector="Drishti Python AST analyzer",
        surrounding_context=context,
        evidence={"ast_call": _name(node.func) if isinstance(node, ast.Call) else type(node).__name__},
        attack_scenario=f"Untrusted input may reach the {vuln_type.lower()} operation at {filename}:{line}.",
        explanation=recommendation,
        recommendation=recommendation,
    )


def analyze_python(code: str, filename: str) -> list[FindingSchema]:
    try:
        tree = ast.parse(code, filename=filename)
    except SyntaxError:
        return []

    findings: list[FindingSchema] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _name(node.func)
        if name in {"eval", "exec"}:
            findings.append(_finding(code, filename, node, "DRISHTI-EVAL-022", "critical", "Dynamic code execution", "CWE-95", "Avoid eval/exec for data processing. Use a constrained parser or an allowlisted operation."))
        elif name == "os.system":
            findings.append(_finding(code, filename, node, "DRISHTI-SHELL-006", "high", "Command injection", "CWE-78", "Pass an argument list to subprocess with shell=False and validate values at the boundary."))
        elif name == "yaml.load":
            safe_loader = any(keyword.arg == "Loader" and _name(keyword.value).endswith("SafeLoader") for keyword in node.keywords)
            if not safe_loader:
                findings.append(_finding(code, filename, node, "DRISHTI-YAML-026", "high", "Unsafe YAML loading", "CWE-502", "Use yaml.safe_load or an explicit SafeLoader for untrusted YAML."))
        elif name in {"pickle.load", "pickle.loads", "marshal.load", "marshal.loads"}:
            findings.append(_finding(code, filename, node, "DRISHTI-DESER-019", "critical", "Insecure deserialization", "CWE-502", "Use a safe, constrained serialization format and never deserialize untrusted objects."))
        elif name == "tempfile.mktemp":
            findings.append(_finding(code, filename, node, "DRISHTI-TEMP-031", "high", "Insecure temporary file", "CWE-377", "Use tempfile.NamedTemporaryFile or mkstemp so creation and ownership are atomic."))
        elif name in {"requests.get", "requests.post", "requests.request", "httpx.get", "httpx.post", "urllib.request.urlopen"}:
            verify = next((keyword.value for keyword in node.keywords if keyword.arg == "verify"), None)
            if isinstance(verify, ast.Constant) and verify.value is False:
                findings.append(_finding(code, filename, node, "DRISHTI-TLS-030", "high", "TLS certificate verification disabled", "CWE-295", "Keep TLS certificate verification enabled and configure a trusted CA when required."))
        elif name == "jwt.decode":
            for keyword in node.keywords:
                if keyword.arg == "options" and isinstance(keyword.value, ast.Dict):
                    for key, value in zip(keyword.value.keys, keyword.value.values):
                        if isinstance(key, ast.Constant) and key.value == "verify_signature" and isinstance(value, ast.Constant) and value.value is False:
                            findings.append(_finding(code, filename, node, "DRISHTI-JWT-029", "high", "JWT signature verification disabled", "CWE-347", "Require signature verification and an explicit algorithm allowlist when decoding JWTs."))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        call_name = _name(node.value.func)
        target_names = {_name(target).lower() for target in node.targets}
        if call_name in {"random.random", "random.randint", "random.randrange"} and any(any(token in target for token in ("token", "secret", "password", "session", "key")) for target in target_names):
            findings.append(_finding(code, filename, node.value, "DRISHTI-RANDOM-028", "high", "Weak randomness for security value", "CWE-338", "Use the secrets module for tokens, session identifiers, passwords, and security keys."))

    return findings


def ast_capabilities() -> dict:
    tree_sitter_installed = importlib.util.find_spec("tree_sitter") is not None
    return {"python_ast": {"installed": True, "executed": True, "status": "available", "runtime": "stdlib ast"}, "tree_sitter": {"installed": tree_sitter_installed, "executed": False, "status": "installed_not_wired" if tree_sitter_installed else "optional_unavailable", "runtime": "not executed"}}
