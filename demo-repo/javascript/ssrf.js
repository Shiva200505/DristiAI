import fetch from "node-fetch";

export async function proxy(url) {
  // VULNERABLE: DRISHTI-SSRF-025 / CWE-918
  return fetch(url);
}

// Expected fix: allowlist hosts and block private address ranges.
