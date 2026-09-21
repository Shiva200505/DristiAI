from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    path: Mapped[str] = mapped_column(String(500))
    language: Mapped[str] = mapped_column(String(40), default="Python")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_scanned: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scans: Mapped[list["Scan"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Scan(Base):
    __tablename__ = "scans"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(40), default="manual")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="running")
    file_scanned: Mapped[str] = mapped_column(String(500))
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    project: Mapped[Project | None] = relationship(back_populates="scans")
    findings: Mapped[list["Finding"]] = relationship(back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int | None] = mapped_column(ForeignKey("scans.id"), nullable=True)
    issue_id: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20))
    vuln_type: Mapped[str] = mapped_column(String(120))
    line_number: Mapped[int] = mapped_column(Integer)
    file_path: Mapped[str] = mapped_column(String(500))
    code_snippet: Mapped[str] = mapped_column(Text)
    cwe_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    explanation: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="OPEN")
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    scan: Mapped[Scan | None] = relationship(back_populates="findings")
    patches: Mapped[list["Patch"]] = relationship(back_populates="finding", cascade="all, delete-orphan")


class Patch(Base):
    __tablename__ = "patches"
    id: Mapped[int] = mapped_column(primary_key=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"))
    original_code: Mapped[str] = mapped_column(Text)
    patched_code: Mapped[str] = mapped_column(Text)
    diff: Mapped[str] = mapped_column(Text, default="")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verification_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    finding: Mapped[Finding] = relationship(back_populates="patches")


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    component: Mapped[str] = mapped_column(String(80))
    backend_used: Mapped[str] = mapped_column(String(80))
    latency_ms: Mapped[float] = mapped_column(Float)
    device_label: Mapped[str] = mapped_column(String(50))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
