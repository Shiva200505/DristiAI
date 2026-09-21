# Three-minute demo guide

## Prepare

```powershell
python scripts/demo_prep.py
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
npm start
```

Install `vscode-extension/` as an extension development instance, open `demo-repo/python/sql_injection.py`, and save after adding a second interpolated SQL line.

## Judge sequence

1. Show the Drishti status bar after save: the extension sends only the changed file to the local backend.
2. Open Live Security and show the critical SQL finding plus the evidence line.
3. Open Patch Review, inspect the before/after diff, and apply it only after review.
4. Re-run verification and show `RESOLVED`.
5. Open Privacy Center and show local-only processing, no external events, and zero egress.
6. Open Performance and point out which values are measured on the development machine and which Snapdragon values are not measured.
