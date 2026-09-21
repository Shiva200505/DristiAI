const lineNumber = (source, index) => source.slice(0, index).split('\n').length;

export function analyzeSource(source, file = 'untitled.py') {
  const findings = [];
  const patterns = [
    { ruleId: 'DRISHTI-SQL-001', regex: /(?:SELECT|INSERT|UPDATE|DELETE)[^\n]*(?:\+|\{|%\s|\.format\()/i, severity: 'critical', title: 'SQL query built from request input', type: 'SQL injection', source: 'deterministic', confidence: 0.98, description: 'The query interpolates user-controlled input directly into a SQL statement. An attacker can alter the query structure and read or modify records outside the intended scope.', recommendation: 'Use a parameterized query and pass user input as a bound value. Keep the query structure constant.', exploit: 'A crafted identifier can change the query predicate or append a second statement.', patch: 'query = "SELECT * FROM users WHERE id = ?"\n    return db.execute(query, (user_id,)).fetchone()' },
    { ruleId: 'DRISHTI-SHELL-006', regex: /subprocess\.[^(]+\([^\n]*shell\s*=\s*True/i, severity: 'high', title: 'Shell command receives untrusted input', type: 'Command injection', source: 'deterministic', confidence: 0.96, description: 'A process invocation combines a shell with a value that may originate outside the trust boundary.', recommendation: 'Pass an argument list with shell=False and validate values at the boundary.', exploit: 'Shell metacharacters in an input value can execute an arbitrary command.', patch: 'subprocess.run(["tool", validated_value], check=True)' },
    { ruleId: 'DRISHTI-SECRET-014', regex: /(?:password|secret|api[_-]?key|token)\s*=\s*["'][^"']+["']/i, severity: 'high', title: 'Credential-like value in source', type: 'Hardcoded secret', source: 'deterministic', confidence: 0.93, description: 'A credential-like value is stored in source code. Secrets can leak through history, logs, or build artifacts.', recommendation: 'Move the value to an environment-backed secret store and rotate the exposed credential.', exploit: 'Anyone with repository or artifact access can reuse the credential outside the intended service boundary.', patch: 'SECRET = os.environ["SECRET"]' },
    { ruleId: 'DRISHTI-XSS-021', regex: /\.innerHTML\s*=|dangerouslySetInnerHTML/i, severity: 'medium', title: 'Unescaped content reaches the DOM', type: 'Cross-site scripting', source: 'deterministic', confidence: 0.91, description: 'User-controlled content is rendered through an unsafe HTML sink without an explicit sanitization boundary.', recommendation: 'Render text through the framework escaping path or sanitize with a trusted allowlist.', exploit: 'A crafted value can inject markup or script into another user’s browser session.', patch: 'preview.textContent = value' }
  ];
  for (const pattern of patterns) {
    const match = source.match(pattern.regex);
    if (!match) continue;
    const line = lineNumber(source, match.index);
    const evidence = source.split('\n')[line - 1]?.trim() || match[0];
    findings.push({ id: `finding-${pattern.ruleId.toLowerCase()}`, ...pattern, file, line, column: Math.max(1, (match.index || 0) - source.lastIndexOf('\n', match.index || 0)), evidence, status: 'open', detectedAt: 'just now', verification: null });
  }
  return findings;
}

export function getPatchForFinding(finding) {
  return { findingId: finding.id, ruleId: finding.ruleId, confidence: finding.confidence, before: finding.evidence, after: finding.patch, rationale: finding.recommendation, checks: ['Rule no longer matches', 'Syntax boundary preserved', 'No new finding introduced'], status: 'candidate' };
}
