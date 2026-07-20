import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from app.db.base import Base
from app.domain.enums import JobType, JobStatus

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    claim_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("claims.id", ondelete="CASCADE"), nullable=True, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    job_type: Mapped[JobType] = mapped_column(nullable=False)
    status: Mapped[JobStatus] = mapped_column(default=JobStatus.PENDING, nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_code: Mapped[str] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str] = mapped_column(String(1024), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("progress >= 0 AND progress <= 100", name="check_job_progress_range"),
    )

    organization: Mapped["Organization"] = relationship(back_populates="jobs")
    claim: Mapped["Claim"] = relationship(back_populates="jobs")
    document: Mapped["Document"] = relationship(back_populates="jobs")
    stages: Mapped[list["JobStage"]] = relationship(back_populates="job", cascade="all, delete-orphan")
