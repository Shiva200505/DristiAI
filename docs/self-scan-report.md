# Drishti self-scan report

Generated: 2026-09-21T18:06:02.428811+00:00

This report is an actual deterministic scan of the repository using `backend.core.scanner`. Optional Semgrep/Bandit/OSV results are not included in this run.

- Scanned files: 66
- Findings: 51
- Errors: 0
- External tools: disabled for reproducible local self-scan

## Scope summary

The scope labels are review aids, not suppressions. Every finding remains listed below.

- application surface requiring review: 23
- scanner implementation self-match: 1
- intentional fixture/test surface: 27

## Application surface requiring review

- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:145` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:146` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:147` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:150` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:159` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:160` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:166` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:189` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:218` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:234` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:244` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:253` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:264` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:333` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:353` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:368` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:384` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:396` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:401` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:415` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:595` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:609` - Cross-site scripting detected by local deterministic rule
- **HIGH** `DRISHTI-SSRF-025` - `vscode-extension\extension.js:31` - Server-side request forgery detected by local deterministic rule

## Scanner implementation self-matches

- `DRISHTI-XSS-021` - `backend\core\scanner.py:18` - rule-pattern self-match; review only if the analyzer implementation changes.

## Intentional fixture/test surface

- `DRISHTI-SQL-001` - `tests\test_backend.py:9` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-SHELL-006` - `tests\test_backend.py:10` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-PATH-008` - `tests\test_backend.py:11` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-SECRET-014` - `tests\test_backend.py:12` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-CRYPTO-018` - `tests\test_backend.py:13` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-DESER-019` - `tests\test_backend.py:14` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-XSS-021` - `tests\test_backend.py:15` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-SSRF-025` - `tests\test_backend.py:16` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-SQL-001` - `tests\test_backend.py:23` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-TLS-030` - `tests\test_backend.py:32` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-YAML-026` - `tests\test_backend.py:32` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-EVAL-022` - `tests\test_backend.py:38` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-SECRET-014` - `tests\test_security_pipeline.py:18` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-DESER-019` - `tests\test_security_pipeline.py:32` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-DESER-019` - `tests\test_security_pipeline.py:33` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-SQL-001` - `tests\test_security_pipeline.py:37` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-XSS-021` - `tests\test_security_pipeline.py:45` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-XSS-021` - `tests\test_security_pipeline.py:46` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-SQL-001` - `workspace\services\auth.py:9` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-SSRF-025` - `demo-repo\javascript\ssrf.js:5` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-XSS-021` - `demo-repo\javascript\xss_reflected.js:3` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-SHELL-006` - `demo-repo\python\command_injection.py:6` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-SECRET-014` - `demo-repo\python\hardcoded_secrets.py:2` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-DESER-019` - `demo-repo\python\insecure_deserialization.py:6` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-PATH-008` - `demo-repo\python\path_traversal.py:7` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-SQL-001` - `demo-repo\python\sql_injection.py:7` - intentional vulnerable sample or scanner test fixture.
- `DRISHTI-CRYPTO-018` - `demo-repo\python\weak_crypto.py:6` - intentional vulnerable sample or scanner test fixture.

## Full deterministic output

- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:145` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:146` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:147` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:150` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:159` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:160` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:166` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:189` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:218` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:234` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:244` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:253` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:264` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:333` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:353` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:368` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:384` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:396` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:401` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:415` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:595` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `public\app.js:609` - Cross-site scripting detected by local deterministic rule
- **CRITICAL** `DRISHTI-SQL-001` - `tests\test_backend.py:9` - SQL injection detected by local deterministic rule
- **HIGH** `DRISHTI-SHELL-006` - `tests\test_backend.py:10` - Command injection detected by local deterministic rule
- **HIGH** `DRISHTI-PATH-008` - `tests\test_backend.py:11` - Path traversal detected by local deterministic rule
- **HIGH** `DRISHTI-SECRET-014` - `tests\test_backend.py:12` - Hardcoded secret detected by local deterministic rule
- **MEDIUM** `DRISHTI-CRYPTO-018` - `tests\test_backend.py:13` - Weak cryptography detected by local deterministic rule
- **CRITICAL** `DRISHTI-DESER-019` - `tests\test_backend.py:14` - Insecure deserialization detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `tests\test_backend.py:15` - Cross-site scripting detected by local deterministic rule
- **HIGH** `DRISHTI-SSRF-025` - `tests\test_backend.py:16` - Server-side request forgery detected by local deterministic rule
- **CRITICAL** `DRISHTI-SQL-001` - `tests\test_backend.py:23` - SQL injection detected by local deterministic rule
- **HIGH** `DRISHTI-TLS-030` - `tests\test_backend.py:32` - TLS certificate verification disabled detected by local deterministic rule
- **HIGH** `DRISHTI-YAML-026` - `tests\test_backend.py:32` - Unsafe YAML loading detected by local deterministic rule
- **CRITICAL** `DRISHTI-EVAL-022` - `tests\test_backend.py:38` - Dynamic code execution detected by local deterministic rule
- **HIGH** `DRISHTI-SECRET-014` - `tests\test_security_pipeline.py:18` - Hardcoded secret detected by local deterministic rule
- **CRITICAL** `DRISHTI-DESER-019` - `tests\test_security_pipeline.py:32` - Insecure deserialization detected by local deterministic rule
- **CRITICAL** `DRISHTI-DESER-019` - `tests\test_security_pipeline.py:33` - Insecure deserialization detected by local deterministic rule
- **CRITICAL** `DRISHTI-SQL-001` - `tests\test_security_pipeline.py:37` - SQL injection detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `tests\test_security_pipeline.py:45` - Cross-site scripting detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `tests\test_security_pipeline.py:46` - Cross-site scripting detected by local deterministic rule
- **HIGH** `DRISHTI-SSRF-025` - `vscode-extension\extension.js:31` - Server-side request forgery detected by local deterministic rule
- **CRITICAL** `DRISHTI-SQL-001` - `workspace\services\auth.py:9` - SQL injection detected by local deterministic rule
- **HIGH** `DRISHTI-SSRF-025` - `demo-repo\javascript\ssrf.js:5` - Server-side request forgery detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `demo-repo\javascript\xss_reflected.js:3` - Cross-site scripting detected by local deterministic rule
- **HIGH** `DRISHTI-SHELL-006` - `demo-repo\python\command_injection.py:6` - Command injection detected by local deterministic rule
- **HIGH** `DRISHTI-SECRET-014` - `demo-repo\python\hardcoded_secrets.py:2` - Hardcoded secret detected by local deterministic rule
- **CRITICAL** `DRISHTI-DESER-019` - `demo-repo\python\insecure_deserialization.py:6` - Insecure deserialization detected by Python AST analysis
- **HIGH** `DRISHTI-PATH-008` - `demo-repo\python\path_traversal.py:7` - Path traversal detected by local deterministic rule
- **CRITICAL** `DRISHTI-SQL-001` - `demo-repo\python\sql_injection.py:7` - SQL injection detected by local deterministic rule
- **MEDIUM** `DRISHTI-CRYPTO-018` - `demo-repo\python\weak_crypto.py:6` - Weak cryptography detected by local deterministic rule
- **MEDIUM** `DRISHTI-XSS-021` - `backend\core\scanner.py:18` - Cross-site scripting detected by local deterministic rule
