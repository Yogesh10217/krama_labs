import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, ForeignKey, DateTime, UniqueConstraint, JSON, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from app.db.base import Base
from app.domain.enums import ExtractionStatus

class ExtractionRun(Base):
    __tablename__ = "extraction_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    classification_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("document_classifications.id", ondelete="CASCADE"), nullable=False, index=True)

    extractor_name: Mapped[str] = mapped_column(String(50), nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(50), nullable=False)
    schema_name: Mapped[str] = mapped_column(String(50), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(50), nullable=False)

    provider: Mapped[str] = mapped_column(String(50), nullable=True)
    model: Mapped[str] = mapped_column(String(100), nullable=True)
    provider_version: Mapped[str] = mapped_column(String(50), nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    request_id: Mapped[str] = mapped_column(String(255), nullable=True)
    finish_reason: Mapped[str] = mapped_column(String(50), nullable=True)
    cached: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=True)
    provider_input_hash: Mapped[str] = mapped_column(String(255), nullable=True)


    status: Mapped[ExtractionStatus] = mapped_column(default=ExtractionStatus.PENDING, nullable=False)
    artifact_storage_key: Mapped[str] = mapped_column(String(1024), nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    fields: Mapped[list["ExtractedField"]] = relationship("ExtractedField", back_populates="extraction_run", cascade="all, delete-orphan")
    classification: Mapped["DocumentClassification"] = relationship("DocumentClassification", backref="extraction_runs")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    extraction_run_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("extraction_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_value: Mapped[str] = mapped_column(String, nullable=True)
    normalized_value: Mapped[str] = mapped_column(String, nullable=True)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    extraction_run: Mapped["ExtractionRun"] = relationship(back_populates="fields")
    evidence: Mapped[list["FieldEvidence"]] = relationship("FieldEvidence", back_populates="extracted_field", cascade="all, delete-orphan")


class FieldEvidence(Base):
    __tablename__ = "field_evidence"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    extracted_field_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("extracted_fields.id", ondelete="CASCADE"), nullable=False, index=True)

    page_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pages.id", ondelete="SET NULL"), nullable=True)
    ocr_region_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("ocr_regions.id", ondelete="SET NULL"), nullable=True)

    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., 'REGION_MATCH', 'PAGE_INFERENCE'
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    extracted_field: Mapped["ExtractedField"] = relationship(back_populates="evidence")
