# Electron desktop shell

The competition-tested renderer is served by the root Node app so the browser and packaged desktop experience share one UI. This Electron shell starts that local server and opens it in a hardened BrowserWindow. The React component is a real same-origin-capable wrapper for future Vite packaging; it does not create a second business-logic path.

```powershell
cd frontend
npm install
npm start
```
