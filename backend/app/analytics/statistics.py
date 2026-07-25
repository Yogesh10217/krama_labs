from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models.analytics import DailyStatistics, OrganizationStatistics

def get_daily_statistics(db: Session, start_date: date, end_date: date) -> List[DailyStatistics]:
    """Retrieve system-wide daily statistics for a date range."""
    return db.query(DailyStatistics).filter(
        DailyStatistics.date >= start_date,
        DailyStatistics.date <= end_date
    ).order_by(desc(DailyStatistics.date)).all()

def get_organization_statistics(db: Session, org_id: str, start_date: date, end_date: date) -> List[OrganizationStatistics]:
    """Retrieve daily statistics for a specific organization."""
    return db.query(OrganizationStatistics).filter(
        OrganizationStatistics.organization_id == org_id,
        OrganizationStatistics.date >= start_date,
        OrganizationStatistics.date <= end_date
    ).order_by(desc(OrganizationStatistics.date)).all()
