"""Approved workspace path handling for API-facing file operations."""

from __future__ import annotations

import os
from pathlib import Path

from backend.config import settings


def resolve_approved_workspace(path: str | Path) -> Path:
    candidate = Path(path).expanduser().resolve()
    allowed = [settings.root.resolve()]
    if settings.workspace_root:
        allowed.append(Path(settings.workspace_root).expanduser().resolve())
    external_opt_in = os.getenv("DRISHTI_ALLOW_EXTERNAL_WORKSPACE", "false").lower() in {"1", "true", "yes"}
    if not external_opt_in and not any(candidate == root or root in candidate.parents for root in allowed):
        raise ValueError("Workspace is outside the approved Drishti root. Configure DRISHTI_WORKSPACE_ROOT or explicitly enable DRISHTI_ALLOW_EXTERNAL_WORKSPACE.")
    if not candidate.is_dir():
        raise ValueError("Workspace path must be an existing local directory.")
    return candidate

