import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, ForeignKey, DateTime, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from app.db.base import Base

class DocumentClassification(Base):
    __tablename__ = "document_classifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    classifier_name: Mapped[str] = mapped_column(String(100), nullable=False)
    classifier_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    
    evidence_json: Mapped[list] = mapped_column(JSON, nullable=True)
    artifact_storage_key: Mapped[str] = mapped_column(String(1024), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("document_id", name="uq_classification_document"),
    )

    organization: Mapped["Organization"] = relationship()
    document: Mapped["Document"] = relationship(back_populates="classification")
