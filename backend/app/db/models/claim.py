import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid
from app.db.base import Base
from app.domain.enums import ClaimStatus, ClaimPriority

class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    external_reference: Mapped[str] = mapped_column(String(255), nullable=True)
    claim_type: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[ClaimStatus] = mapped_column(default=ClaimStatus.DRAFT, nullable=False, index=True)
    priority: Mapped[ClaimPriority] = mapped_column(default=ClaimPriority.NORMAL, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "external_reference", name="uq_claim_org_ext_ref"),
    )

    organization: Mapped["Organization"] = relationship(back_populates="claims")
    documents: Mapped[list["Document"]] = relationship(back_populates="claim")
    jobs: Mapped[list["Job"]] = relationship(back_populates="claim")
    created_by: Mapped["User"] = relationship()
