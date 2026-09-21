# Electron desktop shell

The current competition-tested renderer is served by the root Node app so it can be developed without bundler overhead. This Electron shell starts that local server and opens it in a hardened BrowserWindow. `src/renderer/App.jsx` is the React migration seam for packaging the renderer once the UI components are moved into React.

```powershell
cd frontend
npm install
npm start
```
