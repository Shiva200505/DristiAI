# Security engine

Scanning is layered:

1. Local deterministic rules provide repeatable evidence for the demo classes.
2. Bandit and Semgrep normalize into the same `FindingSchema` when installed.
3. Dependency manifests are inventoried locally and OSV-Scanner can be invoked explicitly.
4. AI explanation is optional context, never the source of truth.

The canonical finding includes rule, CWE/OWASP mapping when reliable, location, language, detector, masked evidence, recommendation, patch state, and verification state. Project scans skip `.git`, dependency directories, build output, caches, binaries, and oversized files. Changed-file scans accept an explicit file list.
