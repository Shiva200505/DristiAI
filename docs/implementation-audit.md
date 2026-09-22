# Drishti AI implementation audit

Audit date: 2026-09-21

This is the current capability boundary. The project reports unavailable optional hardware, tools, and models instead of presenting them as active.

## Implemented

- The Python backend is the authoritative scanner for browser scans, VS Code scans, project scans, patch preview, patch verification, and finding explanations.
- The scanner emits canonical findings with rule ID, CWE, OWASP mapping, evidence, masked snippets, confidence, line/column, source, patch state, and verification state.
- Deterministic rules cover SQL injection, command injection, path traversal, hardcoded secrets, weak cryptography, insecure deserialization, XSS, SSRF-related patterns, unsafe YAML, dynamic execution, disabled TLS verification, insecure temporary files, and disabled JWT verification.
- Python stdlib AST analysis is executed for Python files. Tree-sitter is reported as optional/installed-not-wired when present; it is not falsely reported as an active analyzer.
- Bandit, Semgrep, and OSV-Scanner adapters are capability-gated and explicitly reported as unavailable when not installed.
- The Node realtime gateway proxies canonical FastAPI operations and provides file watching, SSE events, source editing, live findings, patch review, local explanation, and benchmark responses.
- Local chat combines scanner findings with the persisted retrieval index. A configured local provider can return structured grounded output; without one, the API returns retrieval-only context with `requires_review: true`.
- Retrieval is incremental, replaces deleted chunks, stores file hashes/line ranges/symbol metadata, masks secrets before persistence/embedding, and uses lexical plus optional semantic scoring.
- Patch generation is bounded and review-first. Apply requires a source fingerprint, approved workspace path, atomic replacement, rollback copy, and post-patch security/syntax verification.
- The VS Code extension sends document contents to FastAPI, publishes diagnostics, provides a findings tree, and exposes explain/patch/verify commands.
- Model/provider status, model file hashing, runtime diagnostics, self-scan, and CI checks are available through `npm run doctor`, `npm run models:*`, and `npm run self-scan`.

## Partial or intentionally deferred

- The primary browser UI remains the established vanilla JS application. The Electron React shell is real but embeds that UI; a React/TypeScript rewrite and Monaco editor migration are not complete.
- Patch verification performs bounded diff, security re-scan, syntax validation, and new-finding checks. Project test/typecheck execution is not automatic because it requires an explicitly configured, trusted project command and a post-apply transaction policy.
- The semantic classifier and explainer use a provider registry, but this development environment has no generative model installed, so current responses are deterministic and marked for review.
- Model manifests expose runtime/path/format/validation fields, but license metadata, signed packaging, and a validated target-device artifact still require operator-supplied model/package inputs.
- QNN is a capability probe only. It is not treated as a generic text-generation backend.

## Unavailable in this environment

- Snapdragon NPU execution and Qualcomm latency/power/utilization are not measured on this Intel development machine.
- GenieX requires an operator-installed local service and compatible runtime/device.
- QNN requires a compatible ONNX Runtime build, provider libraries, model, and supported device.
- Sentence Transformers embeddings, Bandit, Semgrep, and OSV-Scanner require explicit local installation/configuration.

## Verification commands

```text
npm run verify
python -m unittest discover -s tests -v
npm run doctor
npm run self-scan
```

The generated self-scan report preserves all findings, including intentional demo/test fixtures and scanner-pattern self-matches. Review scope before treating a finding as a production defect.
