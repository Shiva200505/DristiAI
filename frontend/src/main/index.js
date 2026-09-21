const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let serverProcess;

function createWindow() {
  const window = new BrowserWindow({ width: 1440, height: 960, minWidth: 1100, minHeight: 720, backgroundColor: '#09111d', webPreferences: { contextIsolation: true, sandbox: true } });
  window.loadURL(process.env.DRISHTI_UI_URL || 'http://127.0.0.1:4173');
}

app.whenReady().then(() => {
  if (process.env.DRISHTI_SPAWN_SERVER !== '0') serverProcess = spawn(process.execPath, [path.resolve(__dirname, '../../../server.mjs')], { cwd: path.resolve(__dirname, '../../..'), stdio: 'ignore', windowsHide: true });
  createWindow();
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

app.on('window-all-closed', () => { if (serverProcess) serverProcess.kill(); if (process.platform !== 'darwin') app.quit(); });
app.on('before-quit', () => { if (serverProcess) serverProcess.kill(); });
