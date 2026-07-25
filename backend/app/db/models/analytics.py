import uuid
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, Date, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.base import Base

class DailyStatistics(Base):
    """System-wide daily aggregate statistics."""
    __tablename__ = "analytics_daily_statistics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, unique=True, nullable=False)
    
    documents_processed = Column(Integer, default=0)
    pages_processed = Column(Integer, default=0)
    
    ocr_success_count = Column(Integer, default=0)
    ocr_failure_count = Column(Integer, default=0)
    
    extraction_success_count = Column(Integer, default=0)
    validation_failure_count = Column(Integer, default=0)
    
    review_required_count = Column(Integer, default=0)
    auto_approved_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProviderStatistics(Base):
    """Daily statistics per AI Provider."""
    __tablename__ = "analytics_provider_statistics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=False)
    provider_name = Column(String(50), nullable=False)
    
    requests_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    avg_latency_ms = Column(Float, default=0.0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    
    retries = Column(Integer, default=0)
    circuit_breaker_openings = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_provider_stats_date_name', 'date', 'provider_name', unique=True),
    )


class OrganizationStatistics(Base):
    """Daily or absolute statistics per Organization."""
    __tablename__ = "analytics_organization_statistics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    date = Column(Date, nullable=False)
    
    total_documents = Column(Integer, default=0)
    total_pages = Column(Integer, default=0)
    storage_used_bytes = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    
    jobs_processed = Column(Integer, default=0)
    reviews_completed = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_org_stats_org_date', 'organization_id', 'date', unique=True),
    )


class CostStatistics(Base):
    """Daily cost and token usage tracking (often per organization)."""
    __tablename__ = "analytics_cost_statistics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    provider_name = Column(String(50), nullable=False)
    
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_cost_stats_date_org_provider', 'date', 'organization_id', 'provider_name', unique=True),
    )


class SLAStatistics(Base):
    """Daily SLA metrics for the whole system."""
    __tablename__ = "analytics_sla_statistics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, unique=True, nullable=False)
    
    p50_latency_ms = Column(Float, default=0.0)
    p90_latency_ms = Column(Float, default=0.0)
    p95_latency_ms = Column(Float, default=0.0)
    p99_latency_ms = Column(Float, default=0.0)
    
    job_success_rate = Column(Float, default=0.0)
    pipeline_success_rate = Column(Float, default=0.0)
    
    avg_queue_wait_ms = Column(Float, default=0.0)
    avg_processing_time_ms = Column(Float, default=0.0)
    
    worker_utilization_pct = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HistoricalMetric(Base):
    """Generic time-series metric (e.g. for capacity planning or arbitrary counts)."""
    __tablename__ = "analytics_historical_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    
    tags = Column(JSON, default=dict)  # To store flexible metadata
    
    __table_args__ = (
        Index('ix_historical_metrics_name_time', 'metric_name', 'timestamp'),
    )
