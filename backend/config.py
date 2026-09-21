from dataclasses import dataclass
from pathlib import Path
import os


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    database_url: str = os.getenv("DRISHTI_DATABASE_URL", f"sqlite:///{(ROOT / '.drishti' / 'drishti.db').as_posix()}")
    model_path: str | None = os.getenv("DRISHTI_MODEL_PATH")
    local_only: bool = os.getenv("DRISHTI_LOCAL_ONLY", "true").lower() not in {"0", "false", "no"}
    cors_origin: str = os.getenv("DRISHTI_CORS_ORIGIN", "http://localhost:5173")
    scan_timeout_seconds: int = int(os.getenv("DRISHTI_SCAN_TIMEOUT", "30"))


settings = Settings()
