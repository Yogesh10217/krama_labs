import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.domain.enums import ReviewStatus, ReviewDecisionType

class ReviewSession(Base):
    __tablename__ = "review_sessions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True)
    assigned_user_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING_REVIEW, nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)  # Optimistic concurrency control
    
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="review_session")
    decisions = relationship("ReviewDecision", back_populates="review_session", cascade="all, delete-orphan")
    comments = relationship("ReviewComment", back_populates="review_session", cascade="all, delete-orphan")
    history = relationship("ReviewHistory", back_populates="review_session", cascade="all, delete-orphan")


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_session_id = Column(PG_UUID(as_uuid=True), ForeignKey("review_sessions.id", ondelete="CASCADE"), nullable=False)
    validated_field_id = Column(PG_UUID(as_uuid=True), ForeignKey("validated_fields.id", ondelete="CASCADE"), nullable=False)
    
    decision = Column(Enum(ReviewDecisionType), nullable=False)
    corrected_value = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    reviewer_id = Column(PG_UUID(as_uuid=True), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    review_session = relationship("ReviewSession", back_populates="decisions")
    validated_field = relationship("ValidatedField")


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_session_id = Column(PG_UUID(as_uuid=True), ForeignKey("review_sessions.id", ondelete="CASCADE"), nullable=False)
    validated_field_id = Column(PG_UUID(as_uuid=True), ForeignKey("validated_fields.id", ondelete="SET NULL"), nullable=True)
    
    comment = Column(String, nullable=False)
    reviewer_id = Column(PG_UUID(as_uuid=True), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    review_session = relationship("ReviewSession", back_populates="comments")
    validated_field = relationship("ValidatedField")


class ReviewHistory(Base):
    __tablename__ = "review_histories"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_session_id = Column(PG_UUID(as_uuid=True), ForeignKey("review_sessions.id", ondelete="CASCADE"), nullable=False)
    
    event = Column(String, nullable=False)
    actor = Column(String, nullable=False)  # User UUID string or 'SYSTEM'
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    review_session = relationship("ReviewSession", back_populates="history")
