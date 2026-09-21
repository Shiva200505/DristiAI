# VS Code extension

The extension watches saves with a debounce, sends the changed document to the FastAPI `/api/scans/trigger` route, and surfaces a status notification. It uses the official VS Code extension API and does not use the deprecated Webview UI Toolkit. The backend URL is configurable and defaults to `http://127.0.0.1:8000`.

The next native-IDE expansion is diagnostics and CodeActions backed by the same finding/patch contracts. Until those commands are wired, the extension does not pretend that a notification is a full diagnostic provider.
