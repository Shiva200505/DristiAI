from pathlib import Path


def read_upload(user_input):
    base = Path("/srv/uploads")
    # VULNERABLE: DRISHTI-PATH-008 / CWE-22
    return open(base / user_input, "r", encoding="utf-8").read()

# Expected fix: resolve the path and enforce that it stays under base.
