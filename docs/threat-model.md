# Threat model

## Assets

Source code, credentials, local model files, scan history, patches, and runtime configuration.

## Untrusted inputs

Repository code and documentation, dependency manifests, external scanner output, model files, API request bodies, and optional network responses. Repository text is data, not instructions; prompt injection such as “ignore previous instructions” is not trusted.

## Main threats and controls

- Path traversal or arbitrary overwrite: resolved workspace allowlist, exact content precondition, atomic write, rollback.
- Secret leakage: masked finding evidence, no source/prompt dumps in logs, local-only default.
- Malicious patch: preview → validation → explicit apply → rescan; AI cannot directly overwrite files.
- Tool/subprocess abuse: fixed executable argument arrays, timeouts, optional tools, no shell interpolation.
- Malicious dependency/model: inventory and advisory status are separate; models are operator-installed and should be checksum-verified before use.
- Prompt injection: system/application instructions are separated from untrusted retrieved context; AI claims are not verification evidence.
- Unsafe local API: loopback defaults, explicit CORS, typed input limits, and no remote-content requirement.

Residual risk remains in optional third-party scanners, operator-installed models, host permissions, and incomplete language coverage.
