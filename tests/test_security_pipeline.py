import os
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.core.ai.model_registry import InferenceBackend, ModelRegistry
from backend.core.patcher.apply import PatchApplyError, resolve_allowed_path
from backend.core.patcher.apply import apply_patch, sha256_text
from backend.core.patcher.patch_generator import generate_patch
from backend.core.patcher.verifier import verify_patch
from backend.core.scanner import scan_project
from backend.core.security.findings_parser import FindingSchema
from backend.utils.paths import resolve_approved_workspace


class SecurityPipelineTests(unittest.TestCase):
    def test_finding_masks_secret_and_preserves_canonical_fields(self):
        finding = FindingSchema(issue_id="DRISHTI-SECRET-014", severity="high", confidence=0.9, issue_text="secret", line_number=1, file_path="x.py", vuln_type="Hardcoded secret", code_snippet='AWS_SECRET_KEY = "AKIA123456789012"', cwe_id="CWE-798")
        payload = finding.as_dict()
        self.assertIn("REDACTED", payload["code_snippet"])
        self.assertEqual(payload["rule_id"], "DRISHTI-SECRET-014")
        self.assertEqual(payload["owasp_category"], "A07:2021 Identification and Authentication Failures")
        self.assertEqual(payload["status"], "RULE_DETECTED")

    def test_project_scan_supports_changed_file_mode(self):
        root = Path("demo-repo")
        result = scan_project(root, changed_files=["python/sql_injection.py"], use_external_tools=False)
        self.assertEqual(result["scanned_files"], 1)
        self.assertEqual(result["findings"][0]["issue_id"], "DRISHTI-SQL-001")

    def test_patch_requires_review_when_no_safe_template_exists(self):
        finding = FindingSchema(issue_id="DRISHTI-DESER-019", severity="critical", confidence=0.9, issue_text="deserialization", line_number=1, file_path="x.py", vuln_type="Insecure deserialization", code_snippet="pickle.loads(data)")
        patch = generate_patch(finding, "value = pickle.loads(data)")
        self.assertEqual(patch["status"], "requires_review")

    def test_sql_patch_binds_the_interpolated_expression(self):
        source = 'query = f"SELECT * FROM users WHERE id = {user_id}"\nreturn db.execute(query).fetchone()'
        finding = FindingSchema(issue_id="DRISHTI-SQL-001", severity="critical", confidence=0.9, issue_text="sql", line_number=1, file_path="x.py", vuln_type="SQL injection", code_snippet=source.splitlines()[0], cwe_id="CWE-89")
        patch = generate_patch(finding, source)
        self.assertEqual(patch["status"], "candidate")
        self.assertIn("WHERE id = ?", patch["patched_code"])
        self.assertIn("(user_id,)", patch["patched_code"])

    def test_verification_exposes_explicit_checks(self):
        finding = FindingSchema(issue_id="DRISHTI-XSS-021", severity="medium", confidence=0.9, issue_text="xss", line_number=1, file_path="x.js", vuln_type="XSS", code_snippet="preview.innerHTML = value")
        result = verify_patch(finding, "preview.innerHTML = value", "preview.textContent = value", "javascript")
        self.assertEqual(result.verification_status, "VERIFIED_RESOLVED")
        self.assertTrue(any(check["name"] == "security_rule" for check in result.checks))

    def test_runtime_default_is_truthful(self):
        registry = ModelRegistry()
        self.assertIn(registry.device.backend, {InferenceBackend.TEMPLATE_FALLBACK, InferenceBackend.CPU_LLAMA_CPP, InferenceBackend.GENIEX_OPENAI})

    def test_local_only_blocks_remote_geniex(self):
        with patch.dict(os.environ, {"DRISHTI_LOCAL_ONLY": "true", "DRISHTI_GENIEX_BASE_URL": "https://example.invalid"}, clear=False):
            registry = ModelRegistry()
            self.assertFalse(registry.device.available)
            self.assertIn("remote provider blocked", registry.device.reason)

    def test_patch_path_cannot_escape_workspace(self):
        with self.assertRaises(PatchApplyError):
            resolve_allowed_path("../../outside.txt", [Path.cwd()])

    def test_api_workspace_path_must_be_approved(self):
        with self.assertRaises(ValueError):
            resolve_approved_workspace(Path.cwd().parent)

    def test_patch_apply_creates_rollback_and_checks_content(self):
        target = Path("patch-pipeline-test.py")
        original = "value = 1\n"
        rollback_path = None
        try:
            target.write_text(original, encoding="utf-8")
            result = apply_patch(str(target), original, "value = 2\n", sha256_text(original))
            rollback_path = Path(result["rollback_path"])
            self.assertEqual(target.read_text(encoding="utf-8"), "value = 2\n")
            self.assertTrue(rollback_path.is_file())
        finally:
            target.unlink(missing_ok=True)
            if rollback_path:
                rollback_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
