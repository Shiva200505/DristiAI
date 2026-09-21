# Patch and verification

Patch preview returns original code, proposed code, unified diff, confidence, method, explanation, and source finding. Structured templates are used only for narrow transformations; unsupported findings remain `requires_review`. AI output must be reviewed before application.

Apply checks the approved workspace boundary, exact original content, optional SHA-256 fingerprint, and non-empty change. It writes a rollback copy before an atomic replacement. Verification then runs the canonical scanner and language syntax checks. Results distinguish `VERIFIED_RESOLVED`, `STILL_VULNERABLE`, `NEW_FINDINGS_INTRODUCED`, `PATCH_INVALID`, and manual review. The legacy `status` field remains for existing clients.
