export function renderProfile(profile, preview) {
  // VULNERABLE: DRISHTI-XSS-021 / CWE-79
  preview.innerHTML = profile.bio;
}

// Expected fix: render untrusted content through textContent or a trusted sanitizer.
