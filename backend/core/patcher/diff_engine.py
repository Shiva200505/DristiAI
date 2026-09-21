import difflib


def unified_diff(original: str, patched: str, filename: str = "source") -> str:
    return "".join(difflib.unified_diff(original.splitlines(True), patched.splitlines(True), fromfile=f"{filename} (before)", tofile=f"{filename} (after)"))
