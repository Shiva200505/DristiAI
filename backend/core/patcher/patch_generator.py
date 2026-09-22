import re
from backend.core.patcher.diff_engine import unified_diff
from backend.core.security.findings_parser import FindingSchema

MAX_PATCH_LINES = 120
MAX_CHANGED_LINES = 80


def generate_patch(finding: FindingSchema, original_code: str) -> dict:
    replacement = original_code
    method = "manual_review"
    explanation = finding.recommendation or finding.explanation
    if finding.issue_id == "DRISHTI-SQL-001":
        match = re.search(r"(?m)^(\s*query\s*=\s*)f(['\"])(.*?)(?:\2)$", original_code)
        expression = re.search(r"\{\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\}", match.group(3)) if match else None
        if match and expression and re.search(r"\.execute\(\s*query\s*\)", original_code):
            safe_query = match.group(3)[:expression.start()] + "?" + match.group(3)[expression.end():]
            candidate_line = f'{match.group(1)}"{safe_query}"'
            replacement = original_code.replace(match.group(0), candidate_line, 1)
            replacement = re.sub(r"\.execute\(\s*query\s*\)", f".execute(query, ({expression.group(1)},))", replacement, count=1)
            method = "structured_sql_parameterization_candidate"
    elif finding.issue_id == "DRISHTI-XSS-021":
        replacement = original_code.replace("innerHTML", "textContent")
        method = "structured_dom_sink_replacement"
    elif finding.issue_id == "DRISHTI-SECRET-014":
        match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(['\"])[^'\"]+\2", original_code)
        if match:
            name = match.group(1)
            replacement = re.sub(rf"{re.escape(name)}\s*=\s*(['\"])[^'\"]+\1", f'{name} = os.environ.get("{name}")', original_code, count=1)
            if "import os" not in replacement:
                replacement = "import os\n" + replacement
            method = "structured_secret_externalization_candidate"
    elif finding.issue_id == "DRISHTI-CRYPTO-018":
        replacement = original_code.replace("hashlib.md5", "hashlib.sha256").replace("hashlib.sha1", "hashlib.sha256")
        method = "structured_hash_upgrade_candidate"
    elif finding.issue_id == "DRISHTI-SHELL-006" and "shell=True" in original_code:
        replacement = original_code.replace(", shell=True", ", shell=False").replace("shell=True", "shell=False")
        method = "structured_shell_flag_candidate"
    diff = unified_diff(original_code, replacement, finding.file_path)
    changed_lines = sum(1 for line in diff.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
    bounded = len(replacement) <= 200_000 and len(diff.splitlines()) <= MAX_PATCH_LINES and changed_lines <= MAX_CHANGED_LINES
    status = "candidate" if replacement != original_code and bounded else "requires_review"
    validation = {"bounded": bounded, "changed_lines": changed_lines, "diff_lines": len(diff.splitlines()), "max_changed_lines": MAX_CHANGED_LINES, "max_diff_lines": MAX_PATCH_LINES}
    return {"original_code": original_code, "patched_code": replacement if bounded else original_code, "diff": diff, "confidence": finding.confidence, "status": status, "method": method, "explanation": explanation, "validation": validation, "source_finding": finding.as_dict()}
