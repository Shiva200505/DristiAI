import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeSource, getPatchForFinding } from '../src/security-engine.mjs';

test('detects interpolated SQL as a deterministic finding', () => {
  const findings = analyzeSource('query = f"SELECT * FROM users WHERE id = {user_id}"', 'auth.py');
  assert.equal(findings[0].ruleId, 'DRISHTI-SQL-001');
  assert.equal(findings[0].severity, 'critical');
  assert.equal(findings[0].line, 1);
});

test('returns no findings for a parameterized query', () => {
  assert.deepEqual(analyzeSource('db.execute("SELECT * FROM users WHERE id = ?", (user_id,))', 'auth.py'), []);
});

test('patch contract includes verification checks', () => {
  const finding = analyzeSource('preview.innerHTML = profile.bio', 'profile.tsx')[0];
  const patch = getPatchForFinding(finding);
  assert.equal(patch.status, 'candidate');
  assert.equal(patch.checks.length, 3);
});
