from datetime import date
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models.analytics import SLAStatistics

def get_sla_statistics(db: Session, start_date: date, end_date: date) -> List[SLAStatistics]:
    """Retrieve system-wide SLA statistics for a given date range."""
    return db.query(SLAStatistics).filter(
        SLAStatistics.date >= start_date,
        SLAStatistics.date <= end_date
    ).order_by(desc(SLAStatistics.date)).all()
