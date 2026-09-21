from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from backend.config import settings


Path(settings.root / ".drishti").mkdir(parents=True, exist_ok=True)
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from backend.database.models import Base
    Base.metadata.create_all(bind=engine)
    migrate_legacy_schema()


def migrate_legacy_schema() -> None:
    """Add additive columns for databases created by the MVP.

    This intentionally avoids destructive migrations. A future release can
    replace it with Alembic once schema history becomes user-managed.
    """
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("findings")}
    additions = {
        "rule_id": "VARCHAR(80)",
        "owasp_category": "VARCHAR(160)",
        "column_number": "INTEGER",
        "language": "VARCHAR(40)",
        "detector": "VARCHAR(120)",
        "source": "VARCHAR(40)",
        "evidence": "TEXT",
        "attack_scenario": "TEXT",
        "recommendation": "TEXT",
        "patch_status": "VARCHAR(40) DEFAULT 'NOT_PROPOSED'",
        "verification_status": "VARCHAR(40) DEFAULT 'NOT_RUN'",
        "verification_results": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    }
    if additions:
        with engine.begin() as connection:
            for name, declaration in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE findings ADD COLUMN {name} {declaration}"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
