import http from 'node:http';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir, readdir, stat } from 'node:fs/promises';
import { existsSync, watch } from 'node:fs';
import { extname, join, normalize, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('.', import.meta.url));
const publicDir = join(root, 'public');
const workspaceDir = join(root, 'workspace');
const stateFile = join(root, '.drishti', 'state.json');
const port = Number(process.env.PORT || 4173);
const backendUrl = process.env.DRISHTI_BACKEND_URL || 'http://127.0.0.1:8000';
const requestedWorkspaceRoot = process.env.DRISHTI_WORKSPACE_ROOT?.trim() || '';
const normalizedWorkspaceRoot = requestedWorkspaceRoot.replaceAll('/', '\\').replace(/[\\]+$/, '');
const isWorkspaceExample = !requestedWorkspaceRoot
  || /^(?:[A-Z]:)?\\path\\to\\your\\repository$/i.test(normalizedWorkspaceRoot)
  || /^(?:[A-Z]:)?\\path\\to\\your\\project$/i.test(normalizedWorkspaceRoot);
const requestedWorkspaceExists = requestedWorkspaceRoot && existsSync(requestedWorkspaceRoot);
const workspaceRoot = resolve(isWorkspaceExample || !requestedWorkspaceExists ? workspaceDir : requestedWorkspaceRoot);
const configuredSourceFile = process.env.DRISHTI_SOURCE_FILE || 'services/auth.py';
const supportedSourceExtensions = new Set(['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rb', '.php', '.rs', '.c', '.cpp', '.cs', '.sql', '.html', '.vue', '.svelte', '.kt', '.swift', '.sh', '.bash', '.yaml', '.yml', '.json']);
const ignoredWorkspaceDirectories = new Set(['.git', 'node_modules', '.venv', 'venv', 'dist', 'build', '__pycache__', '.drishti', '.pytest_cache', 'coverage']);

if (requestedWorkspaceRoot && (isWorkspaceExample || !requestedWorkspaceExists)) {
  const reason = isWorkspaceExample ? 'example' : 'missing';
  console.warn(`[Drishti] Ignoring the ${reason} DRISHTI_WORKSPACE_ROOT value; using the included workspace at ${workspaceDir}. Set it to an existing repository path to monitor another project.`);
}

function workspacePath(filePath) {
  const candidate = resolve(workspaceRoot, filePath);
  if (candidate !== workspaceRoot && !candidate.startsWith(`${workspaceRoot}${sep}`)) throw new Error('The requested file is outside the configured workspace.');
  return candidate;
}

function workspaceRelative(filePath) {
  return relative(workspaceRoot, filePath).split(sep).join('/');
}

function isSourceFile(filePath) {
  return supportedSourceExtensions.has(extname(filePath).toLowerCase());
}

function languageForFile(filePath) {
  const extension = extname(filePath).toLowerCase();
  if (extension === '.py') return 'Python';
  if (['.js', '.jsx', '.ts', '.tsx'].includes(extension)) return 'JavaScript';
  return extension.slice(1) || 'text';
}

async function listWorkspaceFiles(directory = workspaceRoot) {
  const files = [];
  let entries;
  try { entries = await readdir(directory, { withFileTypes: true }); } catch { return files; }
  for (const entry of entries) {
    if (entry.name.startsWith('.') && entry.name !== '.env.example') continue;
    if (entry.isDirectory()) {
      if (!ignoredWorkspaceDirectories.has(entry.name)) files.push(...await listWorkspaceFiles(join(directory, entry.name)));
      continue;
    }
    const absolute = join(directory, entry.name);
    if (!isSourceFile(absolute)) continue;
    try {
      const details = await stat(absolute);
      if (details.size <= 200_000) files.push(workspaceRelative(absolute));
    } catch { /* A file may disappear while the workspace is changing. */ }
  }
  return files.sort((left, right) => left.localeCompare(right));
}

const state = {
  project: { name: 'Local workspace', branch: 'local', files: 1, language: 'Python' },
  source: '',
  sourceFile: 'workspace/services/auth.py',
  scan: { status: 'idle', phase: 'ready', startedAt: null, durationMs: null },
  stats: { scanCount: 0, lastScanMs: null },
  findings: [ /* legacy fixture retained only for migration compatibility; runtime state is reset below
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
  */ ],
  activity: [ /* legacy activity fixture disabled; activity is created from real scan events
    { icon: 'shield', title: 'Scan completed', detail: 'services/auth.py • 4 findings', time: '2 min ago', tone: 'teal' },
    { icon: 'check', title: 'Patch verified', detail: 'api/rate_limit.py • DRISHTI-API-003', time: 'Yesterday', tone: 'green' },
    { icon: 'book', title: 'Knowledge indexed', detail: 'payments-api-spec.pdf • 42 sections', time: 'Yesterday', tone: 'purple' },
    { icon: 'cpu', title: 'Runtime checked', detail: 'Local CPU • QNN adapter path documented', time: 'Mon, 09:41', tone: 'amber' }
  */ ]
};
state.project = { name: workspaceRoot.split(sep).pop() || 'Local workspace', branch: process.env.DRISHTI_WORKSPACE_BRANCH || 'local', files: 0, language: 'mixed' };
state.source = '';
state.sourceFile = workspaceRelative(workspacePath(configuredSourceFile));
state.findings = [];
state.activity = [];
state.patchCandidates = new Map();

const eventClients = new Set();
let lastCpuSample = process.cpuUsage();
let lastCpuAt = Date.now();
let watchTimer;
let backendRuntime = null;

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
    mode: backendRuntime?.runtime && backendRuntime.runtime !== 'none' ? backendRuntime.runtime : 'LOCAL_DEVELOPMENT',
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
    const response = await fetch(`${backendUrl}/api/system/runtime`);
    if (response.ok) backendRuntime = await response.json();
  } catch {
    backendRuntime = null;
  }
}

async function backendRequest(path, options = {}) {
  const response = await fetch(`${backendUrl}${path}`, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail?.message || payload.error || `Canonical backend request failed (${response.status})`);
  return payload;
}

function normalizeCanonicalFinding(item) {
  const status = String(item.verification_status || item.status || '').toUpperCase();
  const evidence = typeof item.evidence === 'string' ? item.evidence : item.code_snippet || JSON.stringify(item.evidence || {});
  return {
    id: String(item.id ?? item.fingerprint ?? `${item.issue_id}:${item.file_path}:${item.line_number}`),
    ruleId: item.rule_id || item.issue_id,
    severity: String(item.severity || 'medium').toLowerCase(),
    title: item.issue_text || item.vulnerability_type || item.vuln_type || item.issue_id,
    type: item.vulnerability_type || item.vuln_type || 'Security finding',
    file: item.file_path,
    line: item.line_number,
    column: item.column_number,
    source: item.source === 'ast' ? 'deterministic' : item.source || 'deterministic',
    confidence: Number(item.confidence || 0),
    status: status === 'VERIFIED_RESOLVED' || status === 'PATCH_VERIFIED' || status === 'RESOLVED' ? 'resolved' : 'open',
    detectedAt: 'just now',
    description: item.explanation || item.issue_text || '',
    evidence,
    recommendation: item.recommendation || item.explanation || '',
    exploit: item.attack_scenario || 'Review the source-to-sink path and trust boundary before approving remediation.',
    patch: item.candidate_patch || '',
    verification: item.verification_results || null,
    canonical: item
  };
}

function canonicalFindingPayload(finding) {
  const item = finding.canonical || finding;
  return {
    issue_id: item.issue_id || finding.ruleId,
    severity: item.severity || finding.severity,
    confidence: Number(item.confidence || finding.confidence || 0),
    issue_text: item.issue_text || finding.title,
    line_number: Number(item.line_number || finding.line || 1),
    file_path: item.file_path || finding.file,
    vuln_type: item.vuln_type || item.vulnerability_type || finding.type,
    code_snippet: item.code_snippet || finding.evidence || '',
    cwe_id: item.cwe_id || null,
    source: item.source || 'deterministic',
    explanation: item.explanation || finding.description || '',
    rule_id: item.rule_id || finding.ruleId,
    owasp_category: item.owasp_category || null,
    column_number: item.column_number || finding.column || null,
    language: item.language || 'python',
    detector: item.detector || 'Drishti canonical Python engine',
    surrounding_context: item.surrounding_context || '',
    evidence: item.evidence || { code: finding.evidence },
    attack_scenario: item.attack_scenario || finding.exploit || '',
    recommendation: item.recommendation || finding.recommendation || ''
  };
}

async function requestCanonicalScan(source, file, triggeredBy = 'browser') {
  const started = performance.now();
  const payload = await backendRequest('/api/scans/trigger', {
    method: 'POST',
    body: JSON.stringify({ file_path: file, language: languageForFile(file), code_content: source, triggered_by: triggeredBy, project_root: workspaceRoot })
  });
  return { ...payload, durationMs: Number((performance.now() - started).toFixed(2)), findings: (payload.findings || []).map(normalizeCanonicalFinding) };
}

async function previewCanonicalPatch(finding) {
  const payload = await backendRequest('/api/patches/preview', {
    method: 'POST',
    body: JSON.stringify({ finding: canonicalFindingPayload(finding), original_code: state.source, language: 'python' })
  });
  const candidate = {
    ...payload,
    ruleId: finding.ruleId,
    confidence: finding.confidence,
    before: finding.evidence || finding.canonical?.code_snippet || '',
    after: payload.patched_code || '',
    rationale: payload.explanation || finding.recommendation || 'Review the structured candidate against the canonical scanner evidence.',
    checks: ['Canonical patch generator', 'Source fingerprint required', 'Pre-apply verification required']
  };
  state.patchCandidates.set(String(finding.id), candidate);
  return candidate;
}

function sourceHash(source) {
  return createHash('sha256').update(source, 'utf8').digest('hex');
}

async function persistState() {
  await mkdir(join(root, '.drishti'), { recursive: true });
  await writeFile(stateFile, JSON.stringify({ schemaVersion: 3, workspaceRoot, sourceFile: state.sourceFile, source: state.source, findings: state.findings, activity: state.activity, stats: state.stats }, null, 2));
}

async function hydrateState() {
  const files = await listWorkspaceFiles();
  state.project.files = files.length;
  state.project.language = files.length && files.every(file => extname(file).toLowerCase() === '.py') ? 'Python' : 'mixed';
  if (!files.length) throw new Error(`No supported source files were found in ${workspaceRoot}. Set DRISHTI_WORKSPACE_ROOT to a project containing source files.`);
  if (!files.includes(state.sourceFile)) state.sourceFile = files[0];
  state.source = await readFile(workspacePath(state.sourceFile), 'utf8');
  try {
    const saved = JSON.parse(await readFile(stateFile, 'utf8'));
    if (saved.schemaVersion === 3 && saved.workspaceRoot === workspaceRoot && saved.sourceFile === state.sourceFile && saved.source === state.source) {
      state.findings = saved.findings || [];
      state.activity = saved.activity || [];
      state.stats = { ...state.stats, ...(saved.stats || {}) };
    }
  } catch { /* First run: seed the local workspace. */ }
}

async function scanWorkspace(origin = 'project') {
  if (state.scan.status === 'scanning') return { scanId: null, durationMs: null, findings: state.findings.map(findingSummary), skipped: true };
  const started = Date.now();
  const files = await listWorkspaceFiles();
  state.scan = { status: 'scanning', phase: 'workspace scan started', startedAt: new Date(started).toISOString(), durationMs: null, origin, filesTotal: files.length, filesScanned: 0 };
  broadcast('scan:start', { file: workspaceRoot, origin, scan: state.scan });
  const findings = [];
  for (const [index, file] of files.entries()) {
    try {
      const source = await readFile(workspacePath(file), 'utf8');
      broadcast('scan:stage', { stage: 'deterministic', label: 'Rule analysis', detail: `Scanning ${file}`, file });
      const result = await requestCanonicalScan(source, file, origin);
      findings.push(...result.findings);
      state.scan.filesScanned = index + 1;
      broadcast('findings', { items: findings.map(findingSummary) });
    } catch (error) {
      state.scan = { ...state.scan, status: 'error', phase: `scan failed for ${file}`, error: error.message };
      broadcast('scan:error', { origin, file, message: error.message });
      throw error;
    }
  }
  state.findings = findings;
  state.stats.scanCount += 1;
  state.stats.lastScanMs = Date.now() - started;
  state.scan = { status: 'complete', phase: 'workspace analysis complete', startedAt: new Date(started).toISOString(), durationMs: state.stats.lastScanMs, origin, filesTotal: files.length, filesScanned: files.length };
  state.activity.unshift({ icon: 'shield', title: 'Workspace scan completed', detail: `${files.length} source files · ${findings.length} findings`, time: 'just now', tone: 'teal' });
  state.activity = state.activity.slice(0, 12);
  await persistState();
  const payload = { scanId: `workspace-scan-${Date.now()}`, durationMs: state.stats.lastScanMs, findings: state.findings.map(findingSummary), scan: state.scan };
  broadcast('scan:complete', payload);
  broadcast('findings', { items: payload.findings });
  broadcast('activity', { items: state.activity });
  broadcast('runtime', runtimeMetrics());
  return payload;
}

async function bootstrapCanonicalState() {
  if (!state.source) return;
  try { await scanWorkspace('startup'); return; }
  catch (error) { state.findings = []; state.activity = []; state.scan = { status: 'idle', phase: 'backend required', startedAt: null, durationMs: null, error: error.message }; return; }
  try {
    const result = await requestCanonicalScan(state.source, state.sourceFile, 'startup');
    state.findings = result.findings;
    state.stats.scanCount += 1;
    state.stats.lastScanMs = result.durationMs;
    state.scan = { status: 'complete', phase: 'analysis complete', startedAt: new Date().toISOString(), durationMs: result.durationMs, origin: 'startup' };
    state.activity = [{ icon: 'shield', title: 'Canonical scan completed', detail: `${state.sourceFile} • ${result.findings.length} findings`, time: 'just now', tone: 'teal' }];
    await persistState();
  } catch (error) {
    state.findings = [];
    state.activity = [];
    state.scan = { status: 'idle', phase: 'backend required', startedAt: null, durationMs: null, error: error.message };
  }
}

function json(res, status, payload) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(payload));
}

async function body(req) {
  let raw = '';
  for await (const chunk of req) {
    raw += chunk;
    if (Buffer.byteLength(raw, 'utf8') > 1_000_000) {
      const error = new Error('Request body exceeds the 1 MB limit.');
      error.statusCode = 413;
      throw error;
    }
  }
  try { return raw ? JSON.parse(raw) : {}; } catch {
    const error = new Error('Request body must contain valid JSON.');
    error.statusCode = 400;
    throw error;
  }
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

async function performScan(source, file, origin = 'manual', activate = true) {
  if (state.scan.status === 'scanning') return { scanId: null, durationMs: null, findings: state.findings.map(findingSummary), skipped: true };
  const started = Date.now();
  state.scan = { status: 'scanning', phase: 'change received', startedAt: new Date(started).toISOString(), durationMs: null, origin };
  broadcast('scan:start', { file, origin, scan: state.scan });
  broadcast('scan:stage', { stage: 'deterministic', label: 'Rule analysis', detail: 'Checking changed code locally', file });
  let canonical;
  try {
    canonical = await requestCanonicalScan(source, file, origin === 'file-watch' ? 'file-watch' : 'browser');
  } catch (error) {
    state.scan = { status: 'error', phase: 'canonical backend unavailable', startedAt: new Date(started).toISOString(), durationMs: null, origin, error: error.message };
    broadcast('scan:error', { origin, message: error.message });
    throw error;
  }
  const results = canonical.findings;
  broadcast('scan:stage', { stage: 'context', label: 'Context pass', detail: 'Tracing values across the local file', file });
  if (activate) {
    state.source = source;
    state.sourceFile = workspaceRelative(workspacePath(file));
  }
  const normalizedFile = file.replace(/^workspace[\\/]/, '');
  const previousForFile = state.findings.filter(item => item.file === file || item.file === normalizedFile || item.file.endsWith(`/${normalizedFile}`));
  const existing = new Map(state.findings.filter(item => !previousForFile.includes(item)).map(item => [item.ruleId, item]));
  results.forEach(result => {
    const previous = existing.get(result.ruleId);
    existing.set(result.ruleId, { ...result, id: previous?.id || result.id, detectedAt: 'just now', status: previous?.status === 'resolved' && result.status !== 'open' ? 'resolved' : result.status });
  });
  for (const previous of previousForFile) {
    if (!results.some(result => result.ruleId === previous.ruleId)) {
      existing.set(previous.ruleId, { ...previous, status: 'resolved', detectedAt: 'just now', verification: { status: 'verified', checkedAt: 'just now', remaining: 0 } });
    }
  }
  state.findings = [...existing.values()];
  const durationMs = canonical.durationMs;
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

function queueWatchedScan(changedFile = state.sourceFile) {
  clearTimeout(watchTimer);
  watchTimer = setTimeout(async () => {
    try {
      const changedPath = workspacePath(changedFile);
      if (!isSourceFile(changedPath)) return;
      const source = await readFile(changedPath, 'utf8');
      const relativeFile = workspaceRelative(changedPath);
      const files = await listWorkspaceFiles();
      state.project.files = files.length;
      broadcast('workspace', { root: workspaceRoot, project: state.project, selectedFile: state.sourceFile, files });
      if (relativeFile === state.sourceFile) {
        if (source !== state.source) await performScan(source, relativeFile, 'file-watch');
        broadcast('source:update', { file: state.sourceFile, source });
      } else {
        await performScan(source, relativeFile, 'file-watch', false);
      }
    } catch (error) { broadcast('scan:error', { origin: 'file-watch', message: error.message }); }
  }, 140);
}

async function activateSource(file) {
  const absolute = workspacePath(file);
  const source = await readFile(absolute, 'utf8');
  state.sourceFile = workspaceRelative(absolute);
  state.source = source;
  broadcast('source:update', { file: state.sourceFile, source });
  return { file: state.sourceFile, source };
}

async function api(req, res, pathname) {
  if (pathname === '/api/status' && req.method === 'GET') {
    return json(res, 200, {
      ok: true,
      project: state.project,
      runtime: runtimeMetrics(),
      privacy: { localOnly: true, networkPolicy: 'loopback backend only', externalEgress: 'NOT_MEASURED', lastNetworkEvent: 'No external network events recorded' }
    });
  }
  if (pathname === '/api/events' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-cache', Connection: 'keep-alive', 'X-Accel-Buffering': 'no' });
    eventClients.add(res);
    const files = await listWorkspaceFiles();
    state.project.files = files.length;
    sendEvent(res, 'runtime', runtimeMetrics());
    sendEvent(res, 'workspace', { root: workspaceRoot, project: state.project, selectedFile: state.sourceFile, files });
    sendEvent(res, 'findings', { items: state.findings.map(findingSummary) });
    sendEvent(res, 'activity', { items: state.activity });
    sendEvent(res, 'source:update', { file: state.sourceFile, source: state.source });
    req.on('close', () => eventClients.delete(res));
    return;
  }
  if (pathname === '/api/workspace' && req.method === 'GET') {
    const files = await listWorkspaceFiles();
    state.project.files = files.length;
    return json(res, 200, { root: workspaceRoot, project: state.project, selectedFile: state.sourceFile, files, supportedExtensions: [...supportedSourceExtensions] });
  }
  if (pathname === '/api/source' && req.method === 'GET') {
    const requested = new URL(req.url, `http://${req.headers.host}`).searchParams.get('file');
    if (requested) {
      try { return json(res, 200, { ...(await activateSource(requested)), updatedAt: new Date().toISOString() }); } catch (error) { return json(res, 400, { error: error.message }); }
    }
    return json(res, 200, { file: state.sourceFile, source: state.source, updatedAt: new Date().toISOString() });
  }
  if (pathname === '/api/source' && req.method === 'POST') {
    const input = await body(req);
    if (typeof input.source !== 'string' || input.source.length > 200000) return json(res, 400, { error: 'Source must be a string under 200 KB' });
    if (input.file) state.sourceFile = workspaceRelative(workspacePath(input.file));
    state.source = input.source;
    await writeFile(workspacePath(state.sourceFile), state.source);
    broadcast('source:update', { file: state.sourceFile, source: state.source });
    return json(res, 200, { ok: true, file: state.sourceFile, bytes: Buffer.byteLength(state.source) });
  }
  if (pathname === '/api/findings' && req.method === 'GET') return json(res, 200, { items: state.findings.map(findingSummary) });
  if (pathname === '/api/activity' && req.method === 'GET') return json(res, 200, { items: state.activity });
  if (pathname === '/api/benchmark' && req.method === 'POST') {
    const result = await requestCanonicalScan(state.source, state.sourceFile, 'benchmark');
    return json(res, 200, {
      component: 'scanner',
      durationMs: result.durationMs,
      findings: result.findings.length,
      backend: runtimeMetrics().backend,
      measurementSource: 'LOCAL_DEVELOPMENT',
      measuredOn: 'This development machine'
    });
  }
  if (pathname === '/api/knowledge/index' && req.method === 'POST') {
    try {
      const input = await body(req);
      const response = await fetch(`${backendUrl}/api/knowledge/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_root: workspaceRoot, project_slug: 'browser-workspace', ...input })
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
  }
  if (pathname === '/api/scan-project' && req.method === 'POST') return json(res, 200, await scanWorkspace('manual-project'));
  const patchMatch = pathname.match(/^\/api\/findings\/([^/]+)\/patch$/);
  if (patchMatch && req.method === 'POST') {
    const finding = state.findings.find(item => item.id === patchMatch[1]);
    if (!finding) return json(res, 404, { error: 'Finding not found' });
    try { return json(res, 200, await previewCanonicalPatch(finding)); } catch (error) { return json(res, 503, { error: error.message, code: 'CANONICAL_BACKEND_REQUIRED' }); }
  }
  const explainMatch = pathname.match(/^\/api\/findings\/([^/]+)\/explain$/);
  if (explainMatch && req.method === 'POST') {
    const finding = state.findings.find(item => String(item.id) === explainMatch[1]);
    const backendId = finding?.canonical?.id;
    if (!finding || !backendId) return json(res, 404, { error: 'Canonical finding record not found. Run a fresh scan first.' });
    try {
      const input = await body(req);
      return json(res, 200, await backendRequest(`/api/findings/${encodeURIComponent(backendId)}/explain`, { method: 'POST', body: JSON.stringify({ code_context: state.source, rag_context: input.rag_context || '' }) }));
    } catch (error) { return json(res, 503, { error: error.message, code: 'CANONICAL_BACKEND_REQUIRED' }); }
  }
  const applyMatch = pathname.match(/^\/api\/findings\/([^/]+)\/(apply|verify)$/);
  if (applyMatch && req.method === 'POST') {
    const finding = state.findings.find(item => item.id === applyMatch[1]);
    if (!finding) return json(res, 404, { error: 'Finding not found' });
    const action = applyMatch[2];
    if (action === 'apply') {
      const input = await body(req);
      const candidate = state.patchCandidates.get(String(finding.id)) || await previewCanonicalPatch(finding);
      const currentHash = sourceHash(state.source);
      if (input.expectedSha256 && input.expectedSha256 !== currentHash) return json(res, 409, { error: 'The workspace changed since patch preview. Refresh the finding before applying.', code: 'STALE_PATCH' });
      const applied = await backendRequest('/api/patches/apply', { method: 'POST', body: JSON.stringify({ finding: canonicalFindingPayload(finding), original_code: state.source, patched_code: candidate.patched_code, file_path: state.sourceFile, expected_sha256: currentHash, language: 'python' }) });
      state.source = await readFile(workspacePath(state.sourceFile), 'utf8');
      finding.status = 'patched';
      finding.verification = applied.verification;
      broadcast('source:update', { file: state.sourceFile, source: state.source });
      await persistState();
      return json(res, 200, { finding, verification: applied.verification, patch: applied });
    }
    if (action === 'verify') {
      const scan = await requestCanonicalScan(state.source, state.sourceFile, 'patch-verify');
      const remaining = scan.findings.some(item => item.ruleId === finding.ruleId && item.status !== 'resolved');
      finding.status = remaining ? 'needs-review' : 'resolved';
      finding.verification = { status: remaining ? 'needs-review' : 'verified', checkedAt: 'just now', remaining: remaining ? 1 : 0, scanner: 'canonical-python' };
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
    try {
      return json(res, 200, await backendRequest('/api/chat', { method: 'POST', body: JSON.stringify({ message: String(input.message || ''), project_slug: input.project_slug || 'browser-workspace' }) }));
    } catch (error) {
      return json(res, 503, { error: error.message, code: 'CANONICAL_BACKEND_REQUIRED' });
    }
  }
  return json(res, 404, { error: 'API route not found' });
}

async function serve(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  if (url.pathname.startsWith('/api/')) {
    try { return await api(req, res, url.pathname); }
    catch (error) { return json(res, error.statusCode || 500, { error: error.message || 'Internal server error' }); }
  }
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
await bootstrapCanonicalState();
refreshBackendRuntime();
try {
  watch(workspaceRoot, { recursive: true }, (_event, filename) => {
    if (filename) queueWatchedScan(String(filename));
  });
} catch { /* Recursive file watching is best effort on restricted filesystems. */ }
setInterval(() => broadcast('runtime', runtimeMetrics()), 1000);
setInterval(() => broadcast('heartbeat', { at: new Date().toISOString() }), 15000);
setInterval(refreshBackendRuntime, 5000);
http.createServer(serve).listen(port, () => console.log(`Drishti AI running at http://localhost:${port}`));
