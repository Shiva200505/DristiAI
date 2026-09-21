const vscode = require('vscode');

function activate(context) {
  const backendUrl = () => vscode.workspace.getConfiguration('drishti').get('backendUrl', 'http://127.0.0.1:8000');
  const debounceMs = () => vscode.workspace.getConfiguration('drishti').get('debounceMs', 2000);
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  status.text = '$(shield) Drishti AI'; status.tooltip = 'Local security analysis'; status.show();
  context.subscriptions.push(status);
  let timer;

  async function analyze(document, triggeredBy = 'vscode-save') {
    if (document.uri.scheme !== 'file') return;
    status.text = '$(sync~spin) Drishti: analyzing';
    try {
      const response = await fetch(`${backendUrl()}/api/scans/trigger`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ file_path: vscode.workspace.asRelativePath(document.uri), language: languageOf(document), code_content: document.getText(), triggered_by: triggeredBy }) });
      if (!response.ok) throw new Error(`backend ${response.status}`);
      const payload = await response.json();
      const count = payload.findings.length;
      status.text = count ? '$(warning) Drishti: findings' : '$(check) Drishti: clear';
      if (count) vscode.window.showWarningMessage(`Drishti found ${count} local security finding${count === 1 ? '' : 's'} in ${document.fileName}`);
    } catch (error) {
      status.text = '$(circle-slash) Drishti: offline';
      console.warn(`Drishti backend unavailable: ${error.message}`);
    }
  }

  const saveListener = vscode.workspace.onDidSaveTextDocument(document => { clearTimeout(timer); timer = setTimeout(() => analyze(document), debounceMs()); });
  const fileCommand = vscode.commands.registerCommand('drishti.analyzeFile', () => { const editor = vscode.window.activeTextEditor; if (editor) analyze(editor.document, 'manual-command'); });
  const selectionCommand = vscode.commands.registerCommand('drishti.analyzeSelection', () => { const editor = vscode.window.activeTextEditor; if (editor) analyzeSelection(editor, analyze); });
  context.subscriptions.push(saveListener, fileCommand, selectionCommand);
}

async function analyzeSelection(editor, analyze) {
  const selection = editor.document.getText(editor.selection);
  if (!selection.trim()) return vscode.window.showInformationMessage('Select code first.');
  const virtual = { uri: editor.document.uri, fileName: editor.document.fileName, getText: () => selection };
  await analyze(virtual, 'manual-selection');
}

function languageOf(document) { return document.languageId === 'javascript' || document.languageId === 'typescript' ? 'JavaScript' : document.languageId || 'text'; }
function deactivate() {}
module.exports = { activate, deactivate };
