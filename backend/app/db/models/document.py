import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from app.db.base import Base
from app.domain.enums import DocumentStatus

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    claim_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("claims.id", ondelete="RESTRICT"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=True)
    file_extension: Mapped[str] = mapped_column(String(20), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=True)
    checksum: Mapped[str] = mapped_column(String(255), nullable=True)
    document_type: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(default=DocumentStatus.REGISTERED, nullable=False, index=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_documents_claim_id_checksum", "claim_id", "checksum"),
    )

    organization: Mapped["Organization"] = relationship(back_populates="documents")
    claim: Mapped["Claim"] = relationship(back_populates="documents")
    pages: Mapped[list["Page"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    jobs: Mapped[list["Job"]] = relationship(back_populates="document")
    classification: Mapped["DocumentClassification"] = relationship(back_populates="document", uselist=False, cascade="all, delete-orphan")
    review_session = relationship("ReviewSession", back_populates="document", uselist=False, cascade="all, delete-orphan")
