import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from app.db.base import Base


class OCRPageResult(Base):
    """Database model for a page's OCR metadata and canonical JSON artifact pointer.
    
    The actual polygon and coordinate data is stored in the JSON artifact.
    This model serves as the queryable index and relationship anchor.
    """
    __tablename__ = "ocr_page_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    engine: Mapped[str] = mapped_column(String(50), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Fast-access derived metadata
    full_text: Mapped[str] = mapped_column(String, nullable=False)
    region_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Pointer to the StorageProvider key containing the full canonical JSON
    artifact_storage_key: Mapped[str] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    page: Mapped["Page"] = relationship("Page", backref="ocr_result")
    regions: Mapped[list["OCRRegion"]] = relationship("OCRRegion", back_populates="ocr_result", cascade="all, delete-orphan", order_by="OCRRegion.reading_order")


class OCRRegion(Base):
    """Database model for an individual OCR region (e.g. text line or block).
    
    Coordinates are normalized (0.0 to 1.0) based on page width/height.
    Origin (0,0) is top-left.
    """
    __tablename__ = "ocr_regions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ocr_result_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("ocr_page_results.id", ondelete="CASCADE"), nullable=False, index=True)
    
    region_index: Mapped[int] = mapped_column(Integer, nullable=False)
    reading_order: Mapped[int] = mapped_column(Integer, nullable=False)
    
    text: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Normalized bounding box
    x1: Mapped[float] = mapped_column(Float, nullable=False)
    y1: Mapped[float] = mapped_column(Float, nullable=False)
    x2: Mapped[float] = mapped_column(Float, nullable=False)
    y2: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Optional serialized polygon [[x,y],...]
    polygon_json: Mapped[str] = mapped_column(String, nullable=True)
    
    region_type: Mapped[str] = mapped_column(String(50), nullable=False, default="TEXT")

    __table_args__ = (
        UniqueConstraint("ocr_result_id", "region_index", name="uq_ocr_region_index"),
        UniqueConstraint("ocr_result_id", "reading_order", name="uq_ocr_reading_order"),
    )

    ocr_result: Mapped["OCRPageResult"] = relationship(back_populates="regions")
