const vscode = require('vscode');

class FindingsProvider {
  constructor() { this.items = []; this.emitter = new vscode.EventEmitter(); this.onDidChangeTreeData = this.emitter.event; }
  refresh(items) { this.items = items || []; this.emitter.fire(); }
  getTreeItem(item) {
    const tree = new vscode.TreeItem(`${item.severity.toUpperCase()} · ${item.vulnerability_type || item.vuln_type || item.issue_id}`, vscode.TreeItemCollapsibleState.None);
    tree.description = `${item.file_path || item.file}:${item.line_number || item.line}`;
    tree.tooltip = item.explanation || item.issue_text || item.title;
    tree.command = { command: 'drishti.openFinding', title: 'Open finding', arguments: [item] };
    tree.iconPath = new vscode.ThemeIcon(item.severity === 'critical' || item.severity === 'high' ? 'warning' : 'info');
    return tree;
  }
  getChildren() { return this.items; }
}

function activate(context) {
  const backendUrl = () => vscode.workspace.getConfiguration('drishti').get('backendUrl', 'http://127.0.0.1:8000').replace(/\/$/, '');
  const debounceMs = () => vscode.workspace.getConfiguration('drishti').get('debounceMs', 2000);
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  const diagnostics = vscode.languages.createDiagnosticCollection('drishti');
  const findingsProvider = new FindingsProvider();
  const findingsByDocument = new Map();
  let timer;

  status.text = '$(shield) Drishti AI'; status.tooltip = 'Local security analysis'; status.show();
  context.subscriptions.push(status, diagnostics, findingsProvider);

  async function request(path, options = {}) {
    if (typeof fetch !== 'function') throw new Error('This VS Code runtime does not provide fetch.');
    const response = await fetch(`${backendUrl()}${path}`, { headers: { 'content-type': 'application/json' }, ...options });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail?.message || payload.error || `backend ${response.status}`);
    return payload;
  }

  function toDiagnostics(document, findings) {
    const items = findings.map(finding => {
      const line = Math.max(0, Number(finding.line_number || finding.line || 1) - 1);
      const column = Math.max(0, Number(finding.column_number || finding.column || 1) - 1);
      const severity = finding.severity === 'critical' || finding.severity === 'high' ? vscode.DiagnosticSeverity.Error : finding.severity === 'medium' ? vscode.DiagnosticSeverity.Warning : vscode.DiagnosticSeverity.Information;
      const diagnostic = new vscode.Diagnostic(new vscode.Range(line, column, line, Math.max(column + 1, column + 80)), `${finding.issue_id || finding.rule_id}: ${finding.issue_text || finding.title || finding.vulnerability_type}`, severity);
      diagnostic.source = finding.detector || finding.source || 'Drishti';
      diagnostic.code = finding.cwe_id || finding.issue_id || finding.rule_id;
      return diagnostic;
    });
    diagnostics.set(document.uri, items);
  }

  async function analyze(document, triggeredBy = 'vscode-save') {
    if (document.uri.scheme !== 'file') return [];
    status.text = '$(sync~spin) Drishti: analyzing';
    try {
      const payload = await request('/api/scans/trigger', { method: 'POST', body: JSON.stringify({ file_path: vscode.workspace.asRelativePath(document.uri), language: languageOf(document), code_content: document.getText(), triggered_by: triggeredBy }) });
      const findings = payload.findings || [];
      findingsByDocument.set(document.uri.toString(), findings);
      toDiagnostics(document, findings);
      findingsProvider.refresh([...findingsByDocument.values()].flat());
      status.text = findings.length ? '$(warning) Drishti: findings' : '$(check) Drishti: clear';
      if (findings.length) vscode.window.showWarningMessage(`Drishti found ${findings.length} local security finding${findings.length === 1 ? '' : 's'} in ${document.fileName}`);
      return findings;
    } catch (error) {
      status.text = '$(circle-slash) Drishti: offline';
      vscode.window.showErrorMessage(`Drishti backend unavailable: ${error.message}`);
      return [];
    }
  }

  async function explainFinding(finding) {
    const text = finding.explanation || finding.recommendation || finding.issue_text || 'No explanation is available from current evidence.';
    await vscode.window.showInformationMessage(`${finding.issue_id || finding.rule_id}: ${text}`, { modal: false });
  }

  async function previewPatch(finding) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const patch = await request('/api/patches/preview', { method: 'POST', body: JSON.stringify({ finding, original_code: editor.document.getText(), language: languageOf(editor.document) }) });
    const document = await vscode.workspace.openTextDocument({ language: languageOf(editor.document), content: `// Drishti candidate: ${patch.method}\n// ${patch.explanation}\n\n${patch.patched_code || patch.after || editor.document.getText()}` });
    await vscode.window.showTextDocument(document, { preview: true, viewColumn: vscode.ViewColumn.Beside });
  }

  async function verifyFinding(finding) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const result = await request('/api/patches/verify', { method: 'POST', body: JSON.stringify({ finding, original_code: editor.document.getText(), language: languageOf(editor.document) }) });
    const statusText = result.verification_status || result.status;
    vscode.window.showInformationMessage(`Drishti verification: ${statusText}. ${result.message}`);
  }

  const saveListener = vscode.workspace.onDidSaveTextDocument(document => { clearTimeout(timer); timer = setTimeout(() => analyze(document), debounceMs()); });
  const fileCommand = vscode.commands.registerCommand('drishti.analyzeFile', () => { const editor = vscode.window.activeTextEditor; if (editor) analyze(editor.document, 'manual-command'); });
  const selectionCommand = vscode.commands.registerCommand('drishti.analyzeSelection', () => { const editor = vscode.window.activeTextEditor; if (editor) analyzeSelection(editor, analyze); });
  const openPanel = vscode.commands.registerCommand('drishti.openPanel', () => vscode.env.openExternal(vscode.Uri.parse('http://127.0.0.1:4173')));
  const openFinding = vscode.commands.registerCommand('drishti.openFinding', finding => explainFinding(finding).catch(error => vscode.window.showErrorMessage(error.message)));
  const explain = vscode.commands.registerCommand('drishti.explainFinding', () => { const finding = currentFinding(findingsByDocument); if (finding) explainFinding(finding); });
  const patch = vscode.commands.registerCommand('drishti.generatePatch', () => { const finding = currentFinding(findingsByDocument); if (finding) previewPatch(finding).catch(error => vscode.window.showErrorMessage(`Patch preview failed: ${error.message}`)); });
  const verify = vscode.commands.registerCommand('drishti.verifyFix', () => { const finding = currentFinding(findingsByDocument); if (finding) verifyFinding(finding).catch(error => vscode.window.showErrorMessage(`Verification failed: ${error.message}`)); });
  const codeActions = vscode.languages.registerCodeActionsProvider(['python', 'javascript', 'typescript'], { provideCodeActions(document) { const finding = (findingsByDocument.get(document.uri.toString()) || [])[0]; if (!finding) return []; return [action('Explain with Drishti', 'drishti.explainFinding', finding), action('Generate secure patch', 'drishti.generatePatch', finding), action('Verify fix', 'drishti.verifyFix', finding)]; } }, { providedCodeActionKinds: [vscode.CodeActionKind.QuickFix] });
  const tree = vscode.window.registerTreeDataProvider('drishti.findings', findingsProvider);
  context.subscriptions.push(saveListener, fileCommand, selectionCommand, openPanel, openFinding, explain, patch, verify, codeActions, tree);
}

function action(title, command, finding) { const result = new vscode.CodeAction(title, vscode.CodeActionKind.QuickFix); result.command = { command, title, arguments: [finding] }; return result; }
function currentFinding(map) { const editor = vscode.window.activeTextEditor; return editor ? (map.get(editor.document.uri.toString()) || [])[0] : null; }
async function analyzeSelection(editor, analyze) { if (!editor.document.getText(editor.selection).trim()) return vscode.window.showInformationMessage('Select code first.'); await analyze(editor.document, 'manual-selection'); }
function languageOf(document) { return document.languageId === 'javascript' || document.languageId === 'typescript' ? document.languageId : document.languageId || 'text'; }
function deactivate() {}
module.exports = { activate, deactivate };
