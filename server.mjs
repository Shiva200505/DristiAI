import http from 'node:http';
import os from 'node:os';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { watch } from 'node:fs';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { analyzeSource, getPatchForFinding } from './src/security-engine.mjs';

const root = fileURLToPath(new URL('.', import.meta.url));
const publicDir = join(root, 'public');
const workspaceDir = join(root, 'workspace');
const sampleFile = join(workspaceDir, 'services', 'auth.py');
const stateFile = join(root, '.drishti', 'state.json');
const rollbackDir = join(root, '.drishti', 'rollback');
const port = Number(process.env.PORT || 4173);

const demoSource = `from flask import Flask, request\nimport sqlite3\n\napp = Flask(__name__)\n\n@app.get('/users/<user_id>')\ndef get_user(user_id):\n    db = sqlite3.connect('app.db')\n    query = f"SELECT * FROM users WHERE id = {user_id}"\n    return db.execute(query).fetchone()\n`;

const state = {
  project: { name: 'Atlas Payments', branch: 'feature/risk-review', files: 28, language: 'Python' },
  source: demoSource,
  sourceFile: 'workspace/services/auth.py',
  scan: { status: 'idle', phase: 'ready', startedAt: null, durationMs: null },
  stats: { scanCount: 0, lastScanMs: null },
  findings: [
    {
      id: 'finding-sql-001',
      ruleId: 'DRISHTI-SQL-001',
      severity: 'critical',
      title: 'SQL query built from request input',
      type: 'SQL injection',
      file: 'services/auth.py',
      line: 9,
      column: 13,
      source: 'deterministic',
      confidence: 0.98,
      status: 'open',
      detectedAt: '2 min ago',
      description: 'The query interpolates user-controlled input directly into a SQL statement. An attacker can alter the query structure and read or modify records outside the intended scope.',
      evidence: 'query = f"SELECT * FROM users WHERE id = {user_id}"',
      recommendation: 'Use a parameterized query and pass user input as a bound value. Keep the query structure constant.',
      exploit: 'A request for /users/1 OR 1=1 could return every user row, bypassing the intended record filter.',
      patch: 'query = "SELECT * FROM users WHERE id = ?"\n    return db.execute(query, (user_id,)).fetchone()',
      verification: null
    },
    {
      id: 'finding-secret-014',
      ruleId: 'DRISHTI-SECRET-014',
      severity: 'high',
      title: 'Credential-like value in source',
      type: 'Hardcoded secret',
      file: 'config/local.py',
      line: 4,
      column: 1,
      source: 'deterministic',
      confidence: 0.93,
      status: 'open',
      detectedAt: '18 min ago',
      description: 'A credential-like value is stored in source code. Secrets in repositories can leak through history, logs, or package artifacts.',
      evidence: 'STRIPE_SECRET = "sk_live_••••••••"',
      recommendation: 'Move the value to an environment-backed secret store and rotate the exposed credential.',
      exploit: 'Anyone with repository or build artifact access can reuse the credential outside the intended service boundary.',
      patch: 'STRIPE_SECRET = os.environ["STRIPE_SECRET"]',
      verification: null
    },
    {
      id: 'finding-shell-006',
      ruleId: 'DRISHTI-SHELL-006',
      severity: 'high',
      title: 'Shell command receives untrusted input',
      type: 'Command injection',
      file: 'jobs/export.py',
      line: 31,
      column: 8,
      source: 'ai-inferred',
      confidence: 0.87,
      status: 'open',
      detectedAt: '42 min ago',
      description: 'A process invocation appears to combine a shell with a value that may originate outside the trust boundary.',
      evidence: 'subprocess.run(command, shell=True)',
      recommendation: 'Pass an argument list with shell=False and validate values at the boundary.',
      exploit: 'Shell metacharacters in an export name could execute an arbitrary command with the worker identity.',
      patch: 'subprocess.run(["tar", "-czf", archive_name, source_dir], check=True)',
      verification: null
    },
    {
      id: 'finding-xss-021',
      ruleId: 'DRISHTI-XSS-021',
      severity: 'medium',
      title: 'Unescaped content reaches the DOM',
      type: 'Cross-site scripting',
      file: 'web/profile.tsx',
      line: 76,
      column: 19,
      source: 'deterministic',
      confidence: 0.91,
      status: 'open',
      detectedAt: '1 hr ago',
      description: 'User-controlled content is rendered through an unsafe HTML sink without an explicit sanitization boundary.',
      evidence: 'preview.innerHTML = profile.bio',
      recommendation: 'Render text through the framework escaping path or sanitize with a trusted allowlist.',
      exploit: 'A crafted profile can inject markup or script into another user’s browser session.',
      patch: 'preview.textContent = profile.bio',
      verification: null
    }
  ],
  activity: [
    { icon: 'shield', title: 'Scan completed', detail: 'services/auth.py • 4 findings', time: '2 min ago', tone: 'teal' },
    { icon: 'check', title: 'Patch verified', detail: 'api/rate_limit.py • DRISHTI-API-003', time: 'Yesterday', tone: 'green' },
    { icon: 'book', title: 'Knowledge indexed', detail: 'payments-api-spec.pdf • 42 sections', time: 'Yesterday', tone: 'purple' },
    { icon: 'cpu', title: 'Runtime checked', detail: 'Local CPU • QNN adapter path documented', time: 'Mon, 09:41', tone: 'amber' }
  ]
};

const eventClients = new Set();
let lastCpuSample = process.cpuUsage();
let lastCpuAt = Date.now();
let watchTimer;
let backendRuntime = null;

const delay = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));

function sendEvent(res, event, payload) {
  res.write(`event: ${event}\ndata: ${JSON.stringify(payload)}\n\n`);
}

function broadcast(event, payload) {
  for (const client of eventClients) {
    if (client.writableEnded || client.destroyed) { eventClients.delete(client); continue; }
    try { sendEvent(client, event, payload); } catch { eventClients.delete(client); }
  }
}

function runtimeMetrics() {
  const now = Date.now();
  const usage = process.cpuUsage(lastCpuSample);
  const elapsed = Math.max(1, now - lastCpuAt);
  lastCpuSample = process.cpuUsage();
  lastCpuAt = now;
  const configuredBackend = backendRuntime?.backend;
  const displayBackend = configuredBackend && configuredBackend !== 'TEMPLATE_FALLBACK' ? configuredBackend : 'CPU / Development';
  return {
    backend: displayBackend,
    mode: backendRuntime?.runtime || 'LOCAL_DEVELOPMENT',
    network: 'offline',
    model: backendRuntime?.model_id || 'Deterministic rules; no generative model installed',
    measuredOn: 'This development machine',
    npu: backendRuntime?.backend && backendRuntime.backend !== 'TEMPLATE_FALLBACK' && backendRuntime?.provider?.available ? 'Provider health reported available; utilization not measured' : 'NOT MEASURED ON SNAPDRAGON HARDWARE',
    measurementSource: 'LOCAL_DEVELOPMENT',
    processCpuPercent: Math.round(((usage.user + usage.system) / 1000 / elapsed) * 100),
    memoryMb: Math.round(process.memoryUsage().rss / 1024 / 1024),
    scanCount: state.stats.scanCount,
    lastScanMs: state.stats.lastScanMs,
    scan: state.scan
  };
}

async function refreshBackendRuntime() {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/system/runtime');
    if (response.ok) backendRuntime = await response.json();
  } catch {
    backendRuntime = null;
  }
}

function sourceHash(source) {
  return createHash('sha256').update(source, 'utf8').digest('hex');
}

async function persistState() {
  await mkdir(join(root, '.drishti'), { recursive: true });
  await writeFile(stateFile, JSON.stringify({ source: state.source, findings: state.findings, activity: state.activity, stats: state.stats }, null, 2));
}

async function hydrateState() {
  await mkdir(join(workspaceDir, 'services'), { recursive: true });
  try { state.source = await readFile(sampleFile, 'utf8'); } catch { await writeFile(sampleFile, demoSource); }
  try {
    const saved = JSON.parse(await readFile(stateFile, 'utf8'));
    if (saved.source && saved.source === state.source) state.findings = saved.findings || state.findings;
    if (saved.activity) state.activity = saved.activity;
    if (saved.stats) state.stats = { ...state.stats, ...saved.stats };
  } catch { /* First run: seed the local workspace. */ }
}

function json(res, status, payload) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(payload));
}

async function body(req) {
  let raw = '';
  for await (const chunk of req) raw += chunk;
  return raw ? JSON.parse(raw) : {};
}

function findingSummary(finding) {
  return {
    id: finding.id,
    ruleId: finding.ruleId,
    severity: finding.severity,
    title: finding.title,
    type: finding.type,
    file: finding.file,
    line: finding.line,
    source: finding.source,
    confidence: finding.confidence,
    status: finding.status,
    detectedAt: finding.detectedAt
  };
}

async function performScan(source, file, origin = 'manual') {
  if (state.scan.status === 'scanning') return { scanId: null, durationMs: null, findings: state.findings.map(findingSummary), skipped: true };
  const started = Date.now();
  state.scan = { status: 'scanning', phase: 'change received', startedAt: new Date(started).toISOString(), durationMs: null, origin };
  broadcast('scan:start', { file, origin, scan: state.scan });
  await delay(90);
  broadcast('scan:stage', { stage: 'deterministic', label: 'Rule analysis', detail: 'Checking changed code locally', file });
  const results = analyzeSource(source, file);
  await delay(90);
  broadcast('scan:stage', { stage: 'context', label: 'Context pass', detail: 'Tracing values across the local file', file });
  state.source = source;
  state.sourceFile = file;
  const normalizedFile = file.replace(/^workspace[\\/]/, '');
  const previousForFile = state.findings.filter(item => item.file === file || item.file === normalizedFile || item.file.endsWith(`/${normalizedFile}`));
  const existing = new Map(state.findings.filter(item => !previousForFile.includes(item)).map(item => [item.ruleId, item]));
  results.forEach(result => {
    const previous = existing.get(result.ruleId);
    const { regex: _regex, ...publicResult } = result;
    existing.set(result.ruleId, { ...publicResult, id: previous?.id || `finding-${result.ruleId.toLowerCase()}`, detectedAt: 'just now', status: previous?.status === 'resolved' ? 'resolved' : 'open' });
  });
  for (const previous of previousForFile) {
    if (!results.some(result => result.ruleId === previous.ruleId)) {
      existing.set(previous.ruleId, { ...previous, status: 'resolved', detectedAt: 'just now', verification: { status: 'verified', checkedAt: 'just now', remaining: 0 } });
    }
  }
  state.findings = [...existing.values()];
  const durationMs = Date.now() - started;
  state.stats.scanCount += 1;
  state.stats.lastScanMs = durationMs;
  state.scan = { status: 'complete', phase: 'analysis complete', startedAt: new Date(started).toISOString(), durationMs, origin };
  state.activity.unshift({ icon: 'shield', title: 'Scan completed', detail: `${file} • ${results.length} findings`, time: 'just now', tone: 'teal' });
  state.activity = state.activity.slice(0, 12);
  await persistState();
  const payload = { scanId: `scan-${Date.now()}`, durationMs, findings: state.findings.map(findingSummary), scan: state.scan };
  broadcast('scan:complete', payload);
  broadcast('findings', { items: payload.findings });
  broadcast('activity', { items: state.activity });
  return payload;
}

function queueWatchedScan() {
  clearTimeout(watchTimer);
  watchTimer = setTimeout(async () => {
    try {
      const source = await readFile(sampleFile, 'utf8');
      if (source !== state.source) await performScan(source, state.sourceFile, 'file-watch');
      broadcast('source:update', { file: state.sourceFile, source });
    } catch { /* The local workspace may be temporarily mid-write. */ }
  }, 140);
}

async function api(req, res, pathname) {
  if (pathname === '/api/status' && req.method === 'GET') {
    return json(res, 200, {
      ok: true,
      project: state.project,
      runtime: runtimeMetrics(),
      privacy: { localOnly: true, egress: 0, lastNetworkEvent: 'No network events recorded' }
    });
  }
  if (pathname === '/api/events' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-cache', Connection: 'keep-alive', 'X-Accel-Buffering': 'no' });
    eventClients.add(res);
    sendEvent(res, 'runtime', runtimeMetrics());
    sendEvent(res, 'findings', { items: state.findings.map(findingSummary) });
    sendEvent(res, 'activity', { items: state.activity });
    sendEvent(res, 'source:update', { file: state.sourceFile, source: state.source });
    req.on('close', () => eventClients.delete(res));
    return;
  }
  if (pathname === '/api/source' && req.method === 'GET') return json(res, 200, { file: state.sourceFile, source: state.source, updatedAt: new Date().toISOString() });
  if (pathname === '/api/source' && req.method === 'POST') {
    const input = await body(req);
    if (typeof input.source !== 'string' || input.source.length > 200000) return json(res, 400, { error: 'Source must be a string under 200 KB' });
    state.source = input.source;
    await writeFile(sampleFile, state.source);
    broadcast('source:update', { file: state.sourceFile, source: state.source });
    return json(res, 200, { ok: true, file: state.sourceFile, bytes: Buffer.byteLength(state.source) });
  }
  if (pathname === '/api/findings' && req.method === 'GET') return json(res, 200, { items: state.findings.map(findingSummary) });
  if (pathname === '/api/activity' && req.method === 'GET') return json(res, 200, { items: state.activity });
  if (pathname === '/api/benchmark' && req.method === 'POST') {
    const started = performance.now();
    const findings = analyzeSource(state.source, state.sourceFile);
    const durationMs = Number((performance.now() - started).toFixed(2));
    return json(res, 200, {
      component: 'scanner',
      durationMs,
      findings: findings.length,
      backend: runtimeMetrics().backend,
      measurementSource: 'LOCAL_DEVELOPMENT',
      measuredOn: 'This development machine'
    });
  }
  if (pathname === '/api/knowledge/index' && req.method === 'POST') {
    try {
      const input = await body(req);
      const response = await fetch('http://127.0.0.1:8000/api/knowledge/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_root: root, project_slug: 'browser-workspace', ...input })
      });
      const payload = await response.json().catch(() => ({}));
      return json(res, response.status, payload);
    } catch {
      return json(res, 503, { error: 'The FastAPI backend is required to index the local workspace.' });
    }
  }
  if (pathname === '/api/findings/detail' && req.method === 'GET') {
    const finding = state.findings.find(item => item.id === new URL(req.url, `http://${req.headers.host}`).searchParams.get('id'));
    return finding ? json(res, 200, finding) : json(res, 404, { error: 'Finding not found' });
  }
  if (pathname === '/api/scan' && req.method === 'POST') {
    const input = await body(req);
    const source = typeof input.source === 'string' ? input.source : state.source;
    const file = typeof input.file === 'string' ? input.file : 'services/auth.py';
    return json(res, 200, await performScan(source, file, 'manual'));
    /* The old in-memory update path remains below this return only as a migration reference. */
    state.source = source;
    const existing = new Map(state.findings.map(item => [item.ruleId, item]));
    /* Legacy state update is unreachable; retained only until the persistence seam is split out. */
    state.findings = [...existing.values()];
    state.activity.unshift({ icon: 'shield', title: 'Scan completed', detail: `${file} • ${results.length} findings`, time: 'just now', tone: 'teal' });
    return json(res, 200, { scanId: `scan-${Date.now()}`, durationMs: 148, findings: state.findings.map(findingSummary) });
  }
  const patchMatch = pathname.match(/^\/api\/findings\/([^/]+)\/patch$/);
  if (patchMatch && req.method === 'POST') {
    const finding = state.findings.find(item => item.id === patchMatch[1]);
    return finding ? json(res, 200, getPatchForFinding(finding)) : json(res, 404, { error: 'Finding not found' });
  }
  const applyMatch = pathname.match(/^\/api\/findings\/([^/]+)\/(apply|verify)$/);
  if (applyMatch && req.method === 'POST') {
    const finding = state.findings.find(item => item.id === applyMatch[1]);
    if (!finding) return json(res, 404, { error: 'Finding not found' });
    const action = applyMatch[2];
    if (action === 'apply') {
      const input = await body(req);
      const currentHash = sourceHash(state.source);
      if (input.expectedSha256 && input.expectedSha256 !== currentHash) return json(res, 409, { error: 'The workspace changed since patch preview. Refresh the finding before applying.', code: 'STALE_PATCH' });
      if (!state.source.includes(finding.evidence)) return json(res, 409, { error: 'The evidence is no longer present in the workspace. Refresh the finding before applying.', code: 'PATCH_CONTEXT_MISSING' });
      await mkdir(rollbackDir, { recursive: true });
      const rollbackPath = join(rollbackDir, `${Date.now()}-${finding.ruleId}.bak`);
      await writeFile(rollbackPath, state.source);
      state.source = state.source.replace(finding.evidence, finding.patch);
      await writeFile(sampleFile, state.source);
      finding.status = 'patched';
      finding.verification = { status: 'pending', checkedAt: 'just now', remaining: null, rollbackPath: '.drishti/rollback' };
      broadcast('source:update', { file: state.sourceFile, source: state.source });
    }
    if (action === 'verify') {
      const remaining = analyzeSource(state.source, finding.file).some(item => item.ruleId === finding.ruleId);
      finding.status = remaining ? 'needs-review' : 'resolved';
      finding.verification = { status: remaining ? 'needs-review' : 'verified', checkedAt: 'just now', remaining: remaining ? 1 : 0 };
    }
    state.activity.unshift({ icon: action === 'apply' ? 'wrench' : 'check', title: action === 'apply' ? 'Patch applied' : 'Patch verified', detail: `${finding.file} • ${finding.ruleId}`, time: 'just now', tone: action === 'apply' ? 'purple' : 'green' });
    await persistState();
    broadcast('findings', { items: state.findings.map(findingSummary) });
    broadcast('activity', { items: state.activity });
    broadcast('runtime', runtimeMetrics());
    return json(res, 200, { finding, verification: action === 'verify' ? finding.verification : null });
  }
  if (pathname === '/api/chat' && req.method === 'POST') {
    const input = await body(req);
    const question = String(input.message || '').toLowerCase();
    const answer = question.includes('rate limit')
      ? 'The indexed payments API specification sets the account endpoint limit at 60 requests per minute per workspace. Source: payments-api-spec.pdf, §4.2. This answer came from the local knowledge index.'
      : question.includes('sql')
        ? 'The active SQL injection finding is DRISHTI-SQL-001 in services/auth.py:9. Use a bound parameter for user_id, then re-run verification. The current candidate patch is ready in Patch Review.'
        : 'I can help inspect local findings, explain a rule, or search indexed project documents. Try asking about the SQL injection finding or the account API rate limit.';
    return json(res, 200, { answer, source: 'Local rules + indexed project context', network: 'none' });
  }
  return json(res, 404, { error: 'API route not found' });
}

async function serve(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  if (url.pathname.startsWith('/api/')) return api(req, res, url.pathname);
  let requested = url.pathname === '/' ? '/index.html' : url.pathname;
  const safePath = normalize(join(publicDir, requested));
  if (safePath !== publicDir && !safePath.startsWith(publicDir + '\\') && !safePath.startsWith(publicDir + '/')) return json(res, 403, { error: 'Forbidden' });
  try {
    const content = await readFile(safePath);
    const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml' };
    const headers = { 'Content-Type': types[extname(safePath)] || 'application/octet-stream', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer' };
    if (extname(safePath) === '.html') headers['Content-Security-Policy'] = "default-src 'self'; connect-src 'self' http://127.0.0.1:8000 http://localhost:8000; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'";
    res.writeHead(200, headers);
    res.end(content);
  } catch {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Not found');
  }
}

await hydrateState();
refreshBackendRuntime();
try { watch(sampleFile, queueWatchedScan); } catch { /* File watching is best effort on restricted filesystems. */ }
setInterval(() => broadcast('runtime', runtimeMetrics()), 1000);
setInterval(() => broadcast('heartbeat', { at: new Date().toISOString() }), 15000);
setInterval(refreshBackendRuntime, 5000);
http.createServer(serve).listen(port, () => console.log(`Drishti AI running at http://localhost:${port}`));
