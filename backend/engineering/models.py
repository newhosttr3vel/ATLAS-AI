"""Persistence models for software-engineering runs."""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.models import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class EngineeringRun(Base):
    __tablename__ = "engineering_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued", index=True)
    mode: Mapped[str] = mapped_column(String(24), nullable=False, default="mock")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    logs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    changed_files: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
