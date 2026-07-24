import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Enum, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.domain.enums import ValidationStatus

class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False)
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True)
    extraction_run_id = Column(PG_UUID(as_uuid=True), ForeignKey("extraction_runs.id", ondelete="CASCADE"), nullable=False)
    
    validator_name = Column(String, nullable=False)
    validator_version = Column(String, nullable=False)
    
    status = Column(String, nullable=False)
    
    artifact_storage_key = Column(String, nullable=False)
    
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", backref="validation_runs")
    extraction_run = relationship("ExtractionRun", backref="validation_runs")
    fields = relationship("ValidatedField", back_populates="validation_run", cascade="all, delete-orphan")

class ValidatedField(Base):
    __tablename__ = "validated_fields"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    validation_run_id = Column(PG_UUID(as_uuid=True), ForeignKey("validation_runs.id", ondelete="CASCADE"), nullable=False)
    extracted_field_id = Column(PG_UUID(as_uuid=True), ForeignKey("extracted_fields.id", ondelete="CASCADE"), nullable=False)
    
    validation_status = Column(Enum(ValidationStatus), nullable=False)
    validation_score = Column(Float, nullable=True)
    validation_reason = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    validation_run = relationship("ValidationRun", back_populates="fields")
    extracted_field = relationship("ExtractedField")
    evidence = relationship("ValidationEvidence", back_populates="validated_field", cascade="all, delete-orphan")

class ValidationEvidence(Base):
    __tablename__ = "validation_evidence"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    validated_field_id = Column(PG_UUID(as_uuid=True), ForeignKey("validated_fields.id", ondelete="CASCADE"), nullable=False)
    
    ocr_region_id = Column(PG_UUID(as_uuid=True), ForeignKey("ocr_regions.id", ondelete="CASCADE"), nullable=False)
    page_id = Column(PG_UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    
    support_type = Column(String, nullable=False)  # e.g., 'exact_match', 'fuzzy_match', 'bounding_box'
    confidence = Column(Float, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    validated_field = relationship("ValidatedField", back_populates="evidence")
    ocr_region = relationship("OCRRegion")
    page = relationship("Page")
