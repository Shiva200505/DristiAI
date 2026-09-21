# Security policy

Drishti processes repository content, which must be treated as untrusted input. Report vulnerabilities in Drishti privately to the repository owner before public disclosure. Do not include real credentials or proprietary source in an issue.

The application is local-first, but the optional OSV-Scanner and model setup paths can make explicit network requests. Local-only mode blocks those paths unless the operator opts in. Patch application requires an exact content match, an approved workspace path, explicit API invocation, and keeps a rollback copy under `.drishti/rollback/`.

Drishti is a security aid, not a guarantee of safety or legal compliance.
