"""Conservative, user-approved patch application with rollback."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import uuid

from backend.config import settings


class PatchApplyError(ValueError):
    pass


def resolve_allowed_path(file_path: str, allowed_roots: list[Path] | None = None) -> Path:
    candidate = Path(file_path)
    if not candidate.is_absolute():
        candidate = settings.root / candidate
    resolved = candidate.resolve()
    roots = [item.resolve() for item in (allowed_roots or [settings.root])]
    if not any(resolved == root or root in resolved.parents for root in roots):
        raise PatchApplyError("The patch target is outside an approved local workspace.")
    return resolved


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def apply_patch(file_path: str, original_code: str, patched_code: str, expected_sha256: str | None = None, allowed_roots: list[Path] | None = None) -> dict:
    target = resolve_allowed_path(file_path, allowed_roots)
    if any(part.lower() in {".git", ".drishti", "node_modules", "__pycache__"} for part in target.parts):
        raise PatchApplyError("The patch target is a protected generated or repository-control path.")
    if target.suffix.lower() in {".pem", ".key", ".p12", ".pfx"} or target.name.lower() in {".env", ".env.local", "id_rsa", "id_ed25519"}:
        raise PatchApplyError("Credential and private-key files cannot be modified by the patch pipeline.")
    if not target.is_file():
        raise PatchApplyError("The patch target does not exist.")
    current = target.read_text(encoding="utf-8")
    current_hash = sha256_text(current)
    if current != original_code:
        raise PatchApplyError("The file changed since the patch preview; refresh the finding before applying.")
    if expected_sha256 and expected_sha256 != current_hash:
        raise PatchApplyError("The expected file fingerprint does not match the current file.")
    if len(original_code) > 200_000 or len(patched_code) > 200_000:
        raise PatchApplyError("Patch input exceeds the 200 KB safety limit.")
    if patched_code == original_code:
        raise PatchApplyError("The candidate patch does not change the file.")
    rollback_dir = settings.root / ".drishti" / "rollback"
    rollback_dir.mkdir(parents=True, exist_ok=True)
    backup = rollback_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}.bak"
    backup.write_text(current, encoding="utf-8")
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.drishti-tmp")
    try:
        temporary.write_text(patched_code, encoding="utf-8", newline="")
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return {"status": "PATCH_APPLIED", "file_path": str(target), "rollback_path": str(backup), "original_sha256": current_hash, "patched_sha256": sha256_text(patched_code)}
