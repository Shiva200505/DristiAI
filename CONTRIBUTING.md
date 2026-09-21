# Contributing to Drishti

Keep changes small, testable, and honest about runtime evidence.

Before opening a change:

```powershell
npm run verify
python -m compileall -q backend scripts benchmarks tests
```

Security changes should include a regression fixture or a unit test. Do not commit `.drishti/`, model files, credentials, generated benchmark output, or source code copied into logs. New providers must expose availability and failure reasons; they must not silently fall back while reporting a faster backend.

Use focused commits such as `feat: add dependency scan adapter` or `fix: reject stale patch targets`. Avoid rewriting unrelated UI or generated files.
