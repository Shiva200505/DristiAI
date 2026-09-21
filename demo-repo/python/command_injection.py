import subprocess


def ping(host):
    # VULNERABLE: DRISHTI-SHELL-006 / CWE-78
    return subprocess.run(f"ping {host}", shell=True, capture_output=True)

# Expected fix: pass a validated argument list with shell=False.
