import unittest
from backend.core.scanner import scan_code, scan_code_with_report
from backend.core.patcher.verifier import verify_patch


class ScannerTests(unittest.TestCase):
    def test_detects_eight_demo_classes(self):
        cases = {
            "DRISHTI-SQL-001": 'query = f"SELECT * FROM users WHERE id = {user_id}"',
            "DRISHTI-SHELL-006": 'subprocess.run(f"ping {host}", shell=True)',
            "DRISHTI-PATH-008": 'open(base / user_input)',
            "DRISHTI-SECRET-014": 'AWS_SECRET_KEY = "AKIA"',
            "DRISHTI-CRYPTO-018": 'hashlib.md5(value)',
            "DRISHTI-DESER-019": 'pickle.loads(data)',
            "DRISHTI-XSS-021": 'preview.innerHTML = profile.bio',
            "DRISHTI-SSRF-025": 'fetch(url)',
        }
        for issue_id, source in cases.items():
            with self.subTest(issue_id=issue_id):
                self.assertEqual(scan_code(source, "fixture.py", use_external_tools=False)[0].issue_id, issue_id)

    def test_parameterized_sql_verifies(self):
        finding = scan_code('query = f"SELECT * FROM users WHERE id = {user_id}"', "fixture.py", use_external_tools=False)[0]
        patched = 'query = "SELECT * FROM users WHERE id = ?"\nreturn db.execute(query, (user_id,))'
        result = verify_patch(finding, finding.code_snippet, patched)
        self.assertEqual(result.status, "RESOLVED")

    def test_sql_rule_does_not_treat_object_update_as_sql(self):
        self.assertFalse(any(item.issue_id == "DRISHTI-SQL-001" for item in scan_code("payload.update({key: value})", "fixture.js", "javascript", use_external_tools=False)))

    def test_python_ast_detects_structured_security_sinks(self):
        source = "import yaml\nvalue = yaml.load(payload)\nresult = httpx.get(url, verify=False)\n"
        findings = scan_code(source, "fixture.py", use_external_tools=False)
        self.assertEqual({item.issue_id for item in findings}, {"DRISHTI-YAML-026", "DRISHTI-TLS-030"})
        self.assertTrue(all(item.detector == "Drishti Python AST analyzer" for item in findings))

    def test_scanner_report_labels_unavailable_optional_tools(self):
        _findings, report = scan_code_with_report("value = eval(data)", "fixture.py", use_external_tools=False)
        self.assertTrue(report["deterministic"]["installed"])
        self.assertFalse(report["bandit"]["executed"])
        self.assertFalse(report["semgrep"]["executed"])
        self.assertIn("duration_ms", report)


if __name__ == "__main__":
    unittest.main()
