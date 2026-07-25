import logging
import asyncio
from datetime import datetime, date, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.db.session import SessionLocal
from app.db.models.document import Document
from app.db.models.page import Page
from app.db.models.job import Job
from app.db.models.organization import Organization
from app.domain.enums import DocumentStatus, JobStatus, PageStatus
from app.db.models.analytics import (
    DailyStatistics, OrganizationStatistics
)

logger = logging.getLogger(__name__)

class AnalyticsAggregator:
    """
    Background job that aggregates transaction data into analytics tables.
    Runs periodically to compute statistics without impacting the main request path.
    """
    
    def __init__(self, interval_seconds: int = 3600):
        self.interval_seconds = interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the background aggregation loop."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Analytics Aggregator started (interval: {self.interval_seconds}s)")

    async def stop(self):
        """Stop the background aggregation loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Analytics Aggregator stopped")

    async def _run_loop(self):
        """Main loop for aggregation."""
        while self._running:
            try:
                logger.info("Starting analytics aggregation run...")
                # Run the synchronous DB operations in a thread pool to avoid blocking the event loop
                await asyncio.to_thread(self.run_aggregation)
                logger.info("Analytics aggregation run completed successfully.")
            except Exception as e:
                logger.error(f"Error during analytics aggregation: {e}", exc_info=True)
            
            await asyncio.sleep(self.interval_seconds)

    def run_aggregation(self):
        """Run all aggregation tasks."""
        db = SessionLocal()
        try:
            today = datetime.now(timezone.utc).date()
            # Compute for today and yesterday to handle late-arriving data/updates
            yesterday = today - timedelta(days=1)
            
            self._aggregate_daily_stats(db, today)
            self._aggregate_daily_stats(db, yesterday)
            
            self._aggregate_org_stats(db, today)
            self._aggregate_org_stats(db, yesterday)
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def _aggregate_daily_stats(self, db: Session, target_date: date):
        """Aggregate system-wide daily statistics."""
        # Check if record exists
        stat = db.query(DailyStatistics).filter(DailyStatistics.date == target_date).first()
        if not stat:
            stat = DailyStatistics(date=target_date)
            db.add(stat)

        # 1. Documents processed (documents created on this date)
        docs_count = db.query(func.count(Document.id)).filter(
            cast(Document.created_at, Date) == target_date
        ).scalar() or 0
        stat.documents_processed = docs_count

        # 2. Pages processed (pages created on this date)
        pages_count = db.query(func.count(Page.id)).filter(
            cast(Page.created_at, Date) == target_date
        ).scalar() or 0
        stat.pages_processed = pages_count

        # 3. Status counts based on jobs or documents
        # For simplicity, we'll look at documents updated on this date that reached specific states
        ocr_success = db.query(func.count(Document.id)).filter(
            cast(Document.updated_at, Date) == target_date,
            Document.status.in_([DocumentStatus.OCR_COMPLETED, DocumentStatus.CLASSIFIED, DocumentStatus.EXTRACTED, DocumentStatus.VALIDATED, DocumentStatus.PROCESSED])
        ).scalar() or 0
        stat.ocr_success_count = ocr_success

        ocr_failed = db.query(func.count(Document.id)).filter(
            cast(Document.updated_at, Date) == target_date,
            Document.status == DocumentStatus.OCR_FAILED
        ).scalar() or 0
        stat.ocr_failure_count = ocr_failed

        ext_success = db.query(func.count(Document.id)).filter(
            cast(Document.updated_at, Date) == target_date,
            Document.status.in_([DocumentStatus.EXTRACTED, DocumentStatus.VALIDATED, DocumentStatus.PROCESSED])
        ).scalar() or 0
        stat.extraction_success_count = ext_success

        val_failed = db.query(func.count(Document.id)).filter(
            cast(Document.updated_at, Date) == target_date,
            Document.status == DocumentStatus.VALIDATION_FAILED
        ).scalar() or 0
        stat.validation_failure_count = val_failed
        
        review_req = db.query(func.count(Document.id)).filter(
            cast(Document.updated_at, Date) == target_date,
            Document.status.in_([DocumentStatus.REVIEW_PENDING, DocumentStatus.UNDER_REVIEW])
        ).scalar() or 0
        stat.review_required_count = review_req

        auto_approved = db.query(func.count(Document.id)).filter(
            cast(Document.updated_at, Date) == target_date,
            Document.status == DocumentStatus.AUTO_APPROVED
        ).scalar() or 0
        stat.auto_approved_count = auto_approved

    def _aggregate_org_stats(self, db: Session, target_date: date):
        """Aggregate per-organization statistics."""
        orgs = db.query(Organization).all()
        
        for org in orgs:
            stat = db.query(OrganizationStatistics).filter(
                OrganizationStatistics.organization_id == str(org.id),
                OrganizationStatistics.date == target_date
            ).first()
            
            if not stat:
                stat = OrganizationStatistics(organization_id=str(org.id), date=target_date)
                db.add(stat)

            # Total docs for this org up to this date
            total_docs = db.query(func.count(Document.id)).filter(
                Document.organization_id == org.id,
                cast(Document.created_at, Date) <= target_date
            ).scalar() or 0
            stat.total_documents = total_docs

            # Total pages
            total_pages = db.query(func.count(Page.id)).join(Document).filter(
                Document.organization_id == org.id,
                cast(Page.created_at, Date) <= target_date
            ).scalar() or 0
            stat.total_pages = total_pages

            # Storage used (sum of document sizes)
            storage_used = db.query(func.sum(Document.size_bytes)).filter(
                Document.organization_id == org.id,
                cast(Document.created_at, Date) <= target_date
            ).scalar() or 0
            stat.storage_used_bytes = storage_used
            
            # Jobs processed on this date
            jobs_processed = db.query(func.count(Job.id)).filter(
                Job.organization_id == org.id,
                cast(Job.created_at, Date) == target_date
            ).scalar() or 0
            stat.jobs_processed = jobs_processed

# Global instance for app lifecycle hooks
aggregator = AnalyticsAggregator()
