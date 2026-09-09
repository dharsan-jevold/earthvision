from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    before_scene_id: Mapped[str] = mapped_column(String(255))
    after_scene_id: Mapped[str] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(50))
    overall_severity: Mapped[str] = mapped_column(String(20))
    total_changed_fraction: Mapped[float] = mapped_column(Float)
    result_json: Mapped[dict] = mapped_column(JSON)  # full AnalyzeResponse payload
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    project: Mapped["Project"] = relationship(back_populates="analyses")
