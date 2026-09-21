const state = {
  view: 'overview',
  findings: [],
  activity: [],
  selectedId: null,
  sourceEditing: false,
  sourceFile: 'workspace/services/auth.py',
  runtime: null,
  source: `from flask import Flask, request\nimport sqlite3\n\napp = Flask(__name__)\n\n@app.get('/users/<user_id>')\ndef get_user(user_id):\n    db = sqlite3.connect('app.db')\n    query = f"SELECT * FROM users WHERE id = {user_id}"\n    return db.execute(query).fetchone()`
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).error || 'Request failed');
  return response.json();
}

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
}

function severityMarkup(severity) {
  return `<span class="severity-label ${severity}">${severity}</span>`;
}

function findingRow(finding, header = false) {
  if (header) return `<div class="finding-row header-row"><div>Finding</div><div>Severity</div><div>Location</div><div>Source</div><div>Confidence</div></div>`;
  const status = finding.status === 'resolved' ? '<span class="status-resolved">Resolved</span>' : '';
  return `<div class="finding-row" data-finding-id="${finding.id}">
    <div class="finding-name"><span class="severity-bar ${finding.severity}"></span><div class="finding-name-copy"><strong>${escapeHtml(finding.title)}</strong><small>${escapeHtml(finding.ruleId)} ${status}</small></div></div>
    <div class="finding-cell">${severityMarkup(finding.severity)}</div>
    <div class="finding-cell"><strong>${escapeHtml(finding.file)}</strong><small>line ${finding.line}</small></div>
    <div class="finding-cell"><span class="source-label">${finding.source === 'ai-inferred' ? 'AI-inferred' : 'Rule-detected'}</span></div>
    <div class="finding-cell confidence">${Math.round(finding.confidence * 100)}%</div><div class="row-arrow">›</div>
  </div>`;
}

function renderFindings() {
  const open = state.findings.filter(item => item.status !== 'resolved');
  $('#overview-findings').innerHTML = findingRow(open[0], true) + open.map(item => findingRow(item)).join('');
  $('#all-findings').innerHTML = findingRow(state.findings[0], true) + state.findings.map(item => findingRow(item)).join('');
  $('#live-finding-list').innerHTML = state.findings.map(item => `<div class="live-finding-item" data-finding-id="${item.id}"><span class="severity-bar ${item.severity}"></span><div class="live-finding-content"><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.file)}:${item.line} · ${escapeHtml(item.type)}</small></div><span class="confidence">${Math.round(item.confidence * 100)}%</span></div>`).join('');
  $$('.finding-row[data-finding-id], .live-finding-item[data-finding-id]').forEach(element => element.addEventListener('click', () => openDetail(element.dataset.findingId)));
  renderEditor();
}

function renderActivity() {
  const list = $('#activity-list');
  if (!list) return;
  list.innerHTML = state.activity.slice(0, 4).map(item => `<div class="activity-row"><span class="activity-icon ${item.tone}">${item.icon === 'check' ? '✓' : item.icon === 'book' ? '▤' : item.icon === 'cpu' ? '⌁' : item.icon === 'wrench' ? '⌘' : '◉'}</span><div class="activity-copy"><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.detail)}</span></div><span class="activity-time">${escapeHtml(item.time)}</span></div>`).join('');
}

function renderEditor() {
  const lines = state.source.split('\n');
  const suspicious = state.findings.find(item => item.ruleId === 'DRISHTI-SQL-001' && item.status !== 'resolved')?.line || 9;
  $('#editor-body').innerHTML = lines.map((line, index) => {
    const safe = escapeHtml(line).replace(/(from|import|def|return|in|as)\b/g, '<span class="syntax-keyword">$1</span>').replace(/(SELECT|FROM|WHERE)/g, '<span class="syntax-function">$1</span>').replace(/(&quot;.*?&quot;|&#39;.*?&#39;)/g, '<span class="syntax-string">$1</span>');
    const marked = index + 1 === suspicious ? safe.replace(/(\{.*?\}|request|user_id)/g, '<span class="syntax-danger">$1</span>') : safe;
    return `<div class="code-line ${index + 1 === suspicious ? 'highlight' : ''}"><span class="line-number">${String(index + 1).padStart(2, '0')}</span><span class="code-text">${marked || ' '}</span></div>`;
  }).join('');
  const sourceInput = $('#source-input');
  if (sourceInput && !state.sourceEditing) sourceInput.value = state.source;
}

function setView(view) {
  state.view = view;
  $$('.view').forEach(element => element.classList.toggle('active', element.id === `view-${view}`));
  $$('.nav-item').forEach(element => element.classList.toggle('active', element.dataset.view === view));
  const labels = { overview: 'Command center', live: 'Live Security', findings: 'Findings', knowledge: 'Local Knowledge', performance: 'Performance', privacy: 'Privacy Center', settings: 'Settings' };
  $('#breadcrumb-current').textContent = labels[view] || 'Command center';
  $('#sidebar')?.classList.remove('open');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function toast(title, message, tone = '') {
  const region = $('#toast-region');
  const element = document.createElement('div');
  element.className = `toast ${tone}`;
  element.innerHTML = `<span class="toast-icon">${tone === 'success' ? '✓' : tone === 'warn' ? '!' : '✦'}</span><div><strong>${escapeHtml(title)}</strong><p>${escapeHtml(message)}</p></div><button class="toast-close">×</button>`;
  $('.toast-close', element).addEventListener('click', () => element.remove());
  region.appendChild(element);
  setTimeout(() => { element.classList.add('out'); setTimeout(() => element.remove(), 250); }, 5000);
}

function closeCommandPalette() {
  $('#command-palette')?.classList.add('hidden');
}

function openCommandPalette() {
  const palette = $('#command-palette');
  const input = $('#command-input');
  const list = $('#command-list');
  if (!palette || !input || !list) return;

  const commands = [
    { label: 'Scan current file', hint: 'Run the local security analyzer', run: async () => { closeCommandPalette(); setView('live'); await runScan(); } },
    { label: 'Open live security', hint: 'Watch the active file and pipeline', run: () => { closeCommandPalette(); setView('live'); } },
    { label: 'Open findings', hint: 'Review and filter detected risks', run: () => { closeCommandPalette(); setView('findings'); } },
    { label: 'Index local workspace', hint: 'Send the workspace to the local knowledge adapter', run: async () => { closeCommandPalette(); setView('knowledge'); await indexWorkspace(); } },
    { label: 'Run local benchmark', hint: 'Measure the deterministic scanner on this machine', run: async () => { closeCommandPalette(); setView('performance'); await runBenchmark(); } },
    { label: 'Open privacy center', hint: 'Review local-only processing status', run: () => { closeCommandPalette(); setView('privacy'); } },
    { label: 'Open settings', hint: 'Configure workspace preferences', run: () => { closeCommandPalette(); setView('settings'); } }
  ];

  const renderCommands = () => {
    const query = input.value.trim().toLowerCase();
    const visible = commands.filter(command => `${command.label} ${command.hint}`.toLowerCase().includes(query));
    list.innerHTML = visible.length
      ? visible.map((command, index) => `<button class="command-item" data-command-index="${commands.indexOf(command)}"><span>${escapeHtml(command.label)}</span><small>${escapeHtml(command.hint)}</small></button>`).join('')
      : '<p class="command-empty">No matching local command.</p>';
    $$('.command-item', list).forEach(button => button.addEventListener('click', () => commands[Number(button.dataset.commandIndex)].run()));
  };

  input.value = '';
  renderCommands();
  input.oninput = renderCommands;
  palette.classList.remove('hidden');
  input.focus();
}

async function indexWorkspace() {
  const buttons = [$('#index-document'), $('#knowledge-refresh')].filter(Boolean);
  const labels = buttons.map(button => button.innerHTML);
  buttons.forEach(button => { button.disabled = true; button.innerHTML = 'Indexing…'; });
  try {
    const result = await api('/api/knowledge/index', { method: 'POST', body: '{}' });
    const chunks = result.indexed_chunks ?? result.chunks_indexed ?? result.chunks;
    const detail = chunks === undefined ? 'The local knowledge adapter accepted the workspace.' : `${chunks} local chunks are ready for retrieval.`;
    toast('Workspace indexed', detail, 'success');
  } catch (error) {
    toast('Indexing unavailable', error.message, 'warn');
  } finally {
    buttons.forEach((button, index) => { button.disabled = false; button.innerHTML = labels[index]; });
  }
}

async function runBenchmark() {
  const button = $('#run-benchmark');
  if (!button) return;
  const label = button.innerHTML;
  button.disabled = true;
  button.innerHTML = 'Measuring…';
  try {
    const result = await api('/api/benchmark', { method: 'POST', body: '{}' });
    const measured = `${result.durationMs} ms`;
    if ($('#benchmark-scan-value')) $('#benchmark-scan-value').textContent = measured;
    if ($('#benchmark-scan-time')) $('#benchmark-scan-time').textContent = 'just now';
    toast('Benchmark complete', `Rule analysis took ${measured} on this development machine.`, 'success');
  } catch (error) {
    toast('Benchmark unavailable', error.message, 'warn');
  } finally {
    button.disabled = false;
    button.innerHTML = label;
  }
}

function toggleButton(toggle, force) {
  if (!toggle) return false;
  const enabled = typeof force === 'boolean' ? force : !toggle.classList.contains('active');
  toggle.classList.toggle('active', enabled);
  toggle.setAttribute('aria-pressed', String(enabled));
  return enabled;
}

function loadSettings() {
  try {
    const settings = JSON.parse(localStorage.getItem('drishti.settings') || '{}');
    if (settings.analysisMode && $('#analysis-mode')) $('#analysis-mode').value = settings.analysisMode;
    if (settings.minimumSeverity && $('#minimum-severity')) $('#minimum-severity').value = settings.minimumSeverity;
    if (typeof settings.scanOnSave === 'boolean') toggleButton($('#scan-on-save-toggle'), settings.scanOnSave);
    if (Array.isArray(settings.languages)) $$('.language-pill').forEach(pill => pill.classList.toggle('active', settings.languages.includes(pill.dataset.language)));
    if (typeof settings.privacyLocalOnly === 'boolean') {
      const enabled = toggleButton($('#privacy-toggle'), settings.privacyLocalOnly);
      const status = $('#privacy-toggle')?.closest('.toggle-wrap')?.querySelector('small');
      if (status) status.textContent = enabled ? 'ON' : 'OFF';
    }
  } catch { /* Browser storage may be disabled; the UI still remains usable. */ }
}

function saveSettings() {
  const settings = {
    analysisMode: $('#analysis-mode')?.value,
    scanOnSave: $('#scan-on-save-toggle')?.classList.contains('active'),
    minimumSeverity: $('#minimum-severity')?.value,
    languages: $$('.language-pill.active').map(pill => pill.dataset.language),
    privacyLocalOnly: $('#privacy-toggle')?.classList.contains('active')
  };
  try { localStorage.setItem('drishti.settings', JSON.stringify(settings)); } catch { /* Keep the session setting in memory. */ }
  toast('Settings saved', 'Workspace preferences are stored in this browser.', 'success');
}

function focusEditor() {
  const panel = $('#editor-panel');
  const button = $('#editor-focus');
  if (!panel || !button) return;
  const focused = panel.classList.toggle('focused');
  button.setAttribute('aria-label', focused ? 'Exit focused editor' : 'Focus editor');
  button.textContent = focused ? '×' : '⌗';
  if (focused) {
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    if (state.sourceEditing) $('#source-input')?.focus();
  }
}

function detailMarkup(finding) {
  const resolved = finding.status === 'resolved';
  return `<div class="detail-kicker">${finding.severity.toUpperCase()} RISK · ${escapeHtml(finding.ruleId)}</div>
    <h2 class="detail-title">${escapeHtml(finding.title)}</h2>
    <div class="detail-meta"><span>${escapeHtml(finding.file)}:${finding.line}</span><span class="separator">/</span><span>${finding.source === 'ai-inferred' ? 'AI-inferred risk' : 'Deterministic rule'}</span><span class="separator">/</span><span>${Math.round(finding.confidence * 100)}% confidence</span></div>
    <div class="detail-section"><h3>What happened</h3><p>${escapeHtml(finding.description)}</p></div>
    <div class="detail-section"><h3>Evidence</h3><div class="evidence-block">${escapeHtml(finding.evidence)}</div></div>
    <div class="detail-section"><div class="exploit-callout"><strong>Why it matters</strong>${escapeHtml(finding.exploit)}</div></div>
    <div class="detail-section"><h3>Secure coding guidance</h3><p>${escapeHtml(finding.recommendation)}</p></div>
    <div class="detail-section source-evidence"><span>Analysis provenance</span><strong>${finding.source === 'ai-inferred' ? 'Local context pass' : 'Local deterministic engine'}</strong></div>
    ${resolved ? `<div class="detail-section"><div class="verification-state"><span>✓</span><div><strong>Verified resolved</strong><small>Post-fix scan found no remaining match · just now</small></div></div></div>` : `<div class="detail-actions"><button class="button ghost" id="detail-dismiss">Dismiss</button><button class="button primary" id="review-patch">Review candidate patch <span>→</span></button></div>`}`;
}

async function openDetail(id) {
  state.selectedId = id;
  const finding = state.findings.find(item => item.id === id);
  if (!finding) return;
  $('#detail-content').innerHTML = detailMarkup(finding);
  $('#detail-overlay').classList.remove('hidden');
  $('#detail-dismiss')?.addEventListener('click', closeDetail);
  $('#review-patch')?.addEventListener('click', () => openPatch(id));
}

function closeDetail() { $('#detail-overlay').classList.add('hidden'); }

async function openPatch(id) {
  closeDetail();
  const finding = state.findings.find(item => item.id === id);
  if (!finding) return;
  try {
    const patch = await api(`/api/findings/${encodeURIComponent(id)}/patch`, { method: 'POST', body: '{}' });
    $('#patch-content').innerHTML = `<div class="patch-header"><div><div class="eyebrow">PATCH REVIEW · ${escapeHtml(patch.ruleId)}</div><h2 class="patch-title">A safer path forward.</h2></div><span class="pill green-pill">${Math.round(patch.confidence * 100)}% confidence</span></div>
      <p class="muted-copy" style="font-size:11px; margin-bottom:18px;">Review the proposed change before it touches your workspace. Drishti will re-run the finding after application.</p>
      <div class="patch-layout"><div class="diff-pane"><header><span>BEFORE</span><span>${escapeHtml(finding.file)}:${finding.line}</span></header><div class="diff-code before"><pre>- ${escapeHtml(patch.before)}</pre></div></div><div class="diff-pane"><header><span>AFTER</span><span>candidate</span></header><div class="diff-code after"><pre>+ ${escapeHtml(patch.after)}</pre></div></div></div>
      <div class="patch-reason"><span>✦</span><div><strong>Why this change</strong><p>${escapeHtml(patch.rationale)}</p></div></div>
      <div class="patch-checks">${patch.checks.map(check => `<span class="check-chip">✓ ${escapeHtml(check)}</span>`).join('')}</div>
      <div class="patch-actions"><button class="button ghost" id="patch-reject">Reject</button><button class="button primary" id="apply-patch">Apply &amp; verify <span>→</span></button></div>`;
    $('#patch-overlay').classList.remove('hidden');
    $('#patch-reject').addEventListener('click', () => { closePatch(); toast('Patch kept in review', 'No files were changed.', ''); });
    $('#apply-patch').addEventListener('click', () => applyAndVerify(id));
  } catch (error) { toast('Patch unavailable', error.message, 'warn'); }
}

function closePatch() { $('#patch-overlay').classList.add('hidden'); }

async function applyAndVerify(id) {
  const button = $('#apply-patch');
  if (button) { button.disabled = true; button.innerHTML = 'Applying locally…'; }
  try {
    await api(`/api/findings/${encodeURIComponent(id)}/apply`, { method: 'POST', body: '{}' });
    toast('Patch applied locally', 'The workspace changed only after your review. Verification is running.', '');
    await new Promise(resolve => setTimeout(resolve, 650));
    const result = await api(`/api/findings/${encodeURIComponent(id)}/verify`, { method: 'POST', body: '{}' });
    const index = state.findings.findIndex(item => item.id === id);
    if (index >= 0) state.findings[index] = result.finding;
    renderFindings();
    renderActivity();
    closePatch();
    toast('Fix verified', `${result.finding.ruleId} is no longer detected by the local analyzer.`, 'success');
  } catch (error) { toast('Verification failed', error.message, 'warn'); if (button) { button.disabled = false; button.innerHTML = 'Apply &amp; verify <span>→</span>'; } }
}

async function runScan() {
  const buttons = [$('#scan-button'), $('#live-scan-button')].filter(Boolean);
  buttons.forEach(button => { button.disabled = true; button.dataset.label = button.innerHTML; button.innerHTML = 'Analyzing…'; });
  try {
    const sourceInput = $('#source-input');
    const source = sourceInput && state.sourceEditing ? sourceInput.value : state.source;
    const result = await api('/api/scan', { method: 'POST', body: JSON.stringify({ source, file: 'services/auth.py' }) });
    state.source = source;
    state.findings = result.findings;
    const activity = await api('/api/activity');
    state.activity = activity.items;
    renderFindings(); renderActivity();
    toast('Scan complete', `${result.findings.filter(item => item.status !== 'resolved').length} open findings · local CPU · ${result.durationMs} ms`, 'success');
  } catch (error) { toast('Scan failed', error.message, 'warn'); }
  buttons.forEach(button => { button.disabled = false; button.innerHTML = button.dataset.label; });
}

function setSourceEditing(editing) {
  state.sourceEditing = editing;
  const body = $('#editor-body');
  const input = $('#source-input');
  const editButton = $('#edit-source');
  const saveButton = $('#save-source');
  if (!body || !input || !editButton || !saveButton) return;
  body.classList.toggle('hidden', editing);
  input.classList.toggle('hidden', !editing);
  editButton.textContent = editing ? 'Cancel' : 'Edit source';
  saveButton.classList.toggle('hidden', !editing);
  if (editing) { input.value = state.source; input.focus(); }
  else renderEditor();
}

async function saveSource() {
  const source = $('#source-input').value;
  try {
    await api('/api/source', { method: 'POST', body: JSON.stringify({ source }) });
    state.source = source;
    setSourceEditing(false);
    await runScan();
  } catch (error) { toast('Source was not saved', error.message, 'warn'); }
}

function setPipelineStage(stage) {
  const title = $('#pipeline-current');
  const detail = $('#pipeline-detail');
  const time = $('#pipeline-current-time');
  const status = $('#live-analysis-status');
  if (stage === 'scanning') { title.textContent = 'Analyzing change'; detail.textContent = 'Local pipeline is running'; time.textContent = 'now'; status.textContent = 'Analyzing locally…'; }
  if (stage === 'deterministic') { title.textContent = 'Rule analysis'; detail.textContent = 'Checking changed code locally'; time.textContent = 'running'; status.textContent = 'Rule analysis running…'; }
  if (stage === 'context') { title.textContent = 'Context pass'; detail.textContent = 'Tracing values across the file'; time.textContent = 'running'; status.textContent = 'Context pass running…'; }
}

function setPipelineComplete(scan) {
  $('#pipeline-current').textContent = 'Analysis complete';
  $('#pipeline-detail').textContent = 'Ready for review';
  $('#pipeline-current-time').textContent = `${scan.durationMs} ms`;
  $('#pipeline-rule-time').textContent = `${scan.durationMs} ms`;
  $('#live-analysis-status').textContent = 'Local analysis complete';
  $('#analysis-time').textContent = `${scan.durationMs} ms analysis`;
}

function applyRuntimeMetrics(metrics) {
  state.runtime = metrics;
  const backend = metrics.backend || 'CPU / Development';
  const model = metrics.model || 'No model reported';
  const measuredOn = metrics.measuredOn || metrics.measurementSource || 'Unknown source';
  if ($('#runtime-top-label')) $('#runtime-top-label').textContent = backend;
  if ($('#pipeline-backend-label')) $('#pipeline-backend-label').textContent = `${backend} backend`;
  if ($('#pipeline-measurement-label')) $('#pipeline-measurement-label').textContent = measuredOn;
  if ($('#runtime-card-title')) $('#runtime-card-title').textContent = backend;
  if ($('#runtime-model-label')) $('#runtime-model-label').textContent = model;
  if ($('#runtime-model-detail')) $('#runtime-model-detail').textContent = metrics.npu || measuredOn;
  if ($('#runtime-backend-label')) $('#runtime-backend-label').textContent = backend;
  if ($('#runtime-network-label')) $('#runtime-network-label').textContent = metrics.network || 'Unknown';
  if ($('#runtime-scan-label')) $('#runtime-scan-label').textContent = metrics.lastScanMs ? `${metrics.lastScanMs} ms` : 'Not recorded';
  if ($('#runtime-measurement-note')) $('#runtime-measurement-note').textContent = metrics.npu || `Measurement source: ${measuredOn}`;
  if ($('#benchmark-scan-value')) $('#benchmark-scan-value').textContent = metrics.lastScanMs ? `${metrics.lastScanMs} ms` : '—';
  if ($('#benchmark-scan-time')) $('#benchmark-scan-time').textContent = metrics.lastScanMs ? 'latest scan' : '—';
  const cpu = Math.min(100, Math.max(0, Number(metrics.processCpuPercent || 0)));
  const memory = Math.min(100, Math.max(0, Number(metrics.memoryMb || 0) / 16));
  const cpuBar = $('#cpu-bar'); const cpuValue = $('#cpu-value'); const memoryBar = $('#memory-bar'); const memoryValue = $('#memory-value');
  if (cpuBar) cpuBar.style.width = `${cpu}%`;
  if (cpuValue) cpuValue.textContent = `${cpu}%`;
  if (memoryBar) memoryBar.style.width = `${memory}%`;
  if (memoryValue) memoryValue.textContent = `${metrics.memoryMb || '—'} MB`;
  if ($('#telemetry-updated')) $('#telemetry-updated').textContent = `Live · ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
  if (metrics.scan?.status === 'scanning') setPipelineStage('scanning');
}

function connectRealtime() {
  if (!window.EventSource) { toast('Realtime unavailable', 'This browser does not support the local event stream.', 'warn'); return; }
  const stream = new EventSource('/api/events');
  stream.addEventListener('runtime', event => applyRuntimeMetrics(JSON.parse(event.data)));
  stream.addEventListener('findings', event => { state.findings = JSON.parse(event.data).items; renderFindings(); });
  stream.addEventListener('activity', event => { state.activity = JSON.parse(event.data).items; renderActivity(); });
  stream.addEventListener('source:update', event => {
    const data = JSON.parse(event.data);
    if (!state.sourceEditing && data.source !== state.source) { state.source = data.source; state.sourceFile = data.file; renderEditor(); }
  });
  stream.addEventListener('scan:start', event => { const data = JSON.parse(event.data); setPipelineStage('scanning'); if (data.origin === 'file-watch') toast('File change detected', 'Drishti started a local analysis automatically.', ''); });
  stream.addEventListener('scan:stage', event => setPipelineStage(JSON.parse(event.data).stage));
  stream.addEventListener('scan:complete', event => {
    const data = JSON.parse(event.data);
    setPipelineComplete(data.scan);
    if (data.scan.origin === 'file-watch') toast('Live scan complete', `${data.findings.filter(item => item.status !== 'resolved').length} open findings in ${data.durationMs} ms.`, 'success');
  });
  stream.onerror = () => { /* EventSource reconnects automatically. */ };
}

async function initialize() {
  try {
    const [findings, activity, source] = await Promise.all([api('/api/findings'), api('/api/activity'), api('/api/source')]);
    state.findings = findings.items;
    state.activity = activity.items;
    state.source = source.source;
    state.sourceFile = source.file;
    renderFindings(); renderActivity();
  } catch { toast('Running in preview mode', 'The local API is not available; showing the workspace shell.', 'warn'); }

  $$('.nav-item').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
  $$('[data-view-target]').forEach(button => button.addEventListener('click', () => setView(button.dataset.viewTarget)));
  $('#scan-button').addEventListener('click', runScan);
  $('#live-scan-button').addEventListener('click', runScan);
  $('#edit-source').addEventListener('click', () => setSourceEditing(!state.sourceEditing));
  $('#save-source').addEventListener('click', saveSource);
  $('#drawer-close').addEventListener('click', closeDetail);
  $('#patch-close').addEventListener('click', closePatch);
  $('#command-close').addEventListener('click', closeCommandPalette);
  $('#detail-overlay').addEventListener('click', event => { if (event.target.id === 'detail-overlay') closeDetail(); });
  $('#patch-overlay').addEventListener('click', event => { if (event.target.id === 'patch-overlay') closePatch(); });
  $('#command-palette').addEventListener('click', event => { if (event.target.id === 'command-palette') closeCommandPalette(); });
  $('#mobile-menu').addEventListener('click', () => $('#sidebar').classList.toggle('open'));
  $('#workspace-switcher').addEventListener('click', openCommandPalette);
  $('#workspace-switcher').addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); openCommandPalette(); } });
  $('#search-button').addEventListener('click', openCommandPalette);
  $('#runtime-info').addEventListener('click', () => {
    setView('performance');
    const runtime = state.runtime || { backend: 'CPU / Development', network: 'offline', measuredOn: 'This development machine' };
    toast('Runtime information', `${runtime.backend} · ${runtime.network} · ${runtime.measuredOn}.`, '');
  });
  $('#user-menu').addEventListener('click', () => { setView('settings'); toast('Workspace profile', 'Priya Shah · Security engineer · local workspace identity.', ''); });
  $('#activity-menu').addEventListener('click', openCommandPalette);
  $('#audit-history').addEventListener('click', () => { setView('overview'); $('#activity-list')?.scrollIntoView({ behavior: 'smooth', block: 'center' }); toast('Audit history', `${state.activity.length} recent local events are shown in the activity trail.`); });
  $('#editor-focus').addEventListener('click', focusEditor);
  $('#editor-menu').addEventListener('click', openCommandPalette);
  $('#filter-button').addEventListener('click', event => {
    const filterBar = $('.filter-bar');
    const visible = !filterBar.classList.contains('hidden');
    filterBar.classList.toggle('hidden', visible);
    event.currentTarget.setAttribute('aria-expanded', String(!visible));
  });
  $('#privacy-toggle').addEventListener('click', event => {
    const enabled = toggleButton(event.currentTarget);
    const status = event.currentTarget.closest('.toggle-wrap')?.querySelector('small');
    if (status) status.textContent = enabled ? 'ON' : 'OFF';
    try {
      const settings = JSON.parse(localStorage.getItem('drishti.settings') || '{}');
      localStorage.setItem('drishti.settings', JSON.stringify({ ...settings, privacyLocalOnly: enabled }));
    } catch { /* Keep the privacy choice for this session. */ }
    toast(enabled ? 'Local-only mode enabled' : 'Local-only mode paused', enabled ? 'Source code will remain on this device.' : 'Review network settings before continuing.', enabled ? 'success' : 'warn');
  });
  $('#index-document').addEventListener('click', indexWorkspace);
  $('#knowledge-refresh').addEventListener('click', indexWorkspace);
  $('#run-benchmark').addEventListener('click', runBenchmark);
  $('#benchmark-guide').addEventListener('click', () => toast('Benchmark guide', 'Run local benchmark for development-machine timing. Snapdragon/QNN values remain unmeasured until a compatible device is connected.', ''));
  $('#save-settings').addEventListener('click', saveSettings);
  $('#scan-on-save-toggle').addEventListener('click', event => toggleButton(event.currentTarget));
  $$('.language-pill').forEach(pill => {
    const toggleLanguage = () => pill.classList.toggle('active');
    pill.addEventListener('click', toggleLanguage);
    pill.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); toggleLanguage(); } });
  });
  $('#knowledge-search').addEventListener('click', askLocalQuestion);
  $('#knowledge-input').addEventListener('keydown', event => { if (event.key === 'Enter') askLocalQuestion(); });
  $$('.filter-tab').forEach(tab => tab.addEventListener('click', () => filterFindings(tab.dataset.filter, tab)));
  $$('.settings-tab').forEach(tab => tab.addEventListener('click', () => { $$('.settings-tab').forEach(item => item.classList.remove('active')); tab.classList.add('active'); toast('Settings section', `${tab.textContent.trim()} preferences are ready to configure.`); }));
  document.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); openCommandPalette(); }
    if (event.key === 'Escape') { closeCommandPalette(); closeDetail(); closePatch(); }
  });
  loadSettings();
  connectRealtime();
}

function filterFindings(filter, selected) {
  $$('.filter-tab').forEach(tab => tab.classList.toggle('active', tab === selected));
  const filtered = filter === 'all' ? state.findings : state.findings.filter(item => item.severity === filter);
  $('#all-findings').innerHTML = findingRow(filtered[0], true) + filtered.map(item => findingRow(item)).join('');
  $$('.finding-row[data-finding-id]', $('#all-findings')).forEach(element => element.addEventListener('click', () => openDetail(element.dataset.findingId)));
}

async function askLocalQuestion() {
  const input = $('#knowledge-input');
  if (!input.value.trim()) return;
  const button = $('#knowledge-search');
  button.disabled = true; button.textContent = '…';
  try {
    const result = await api('/api/chat', { method: 'POST', body: JSON.stringify({ message: input.value }) });
    $('#retrieval-result').classList.remove('hidden');
    $('#retrieval-result').innerHTML = `<div class="result-label">LOCAL ANSWER · ${escapeHtml(result.source.toUpperCase())}</div><p>${escapeHtml(result.answer)}</p><small>Network: ${escapeHtml(result.network)}</small>`;
    toast('Local context found', 'Answer assembled without a network request.', 'success');
  } catch (error) { toast('Question unavailable', error.message, 'warn'); }
  button.disabled = false; button.textContent = '→';
}

initialize();
