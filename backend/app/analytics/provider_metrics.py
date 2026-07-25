from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.db.models.analytics import ProviderStatistics

def get_provider_statistics(db: Session, start_date: date, end_date: date, provider_name: Optional[str] = None) -> List[ProviderStatistics]:
    """Retrieve provider statistics for a given date range."""
    query = db.query(ProviderStatistics).filter(
        ProviderStatistics.date >= start_date,
        ProviderStatistics.date <= end_date
    )
    if provider_name:
        query = query.filter(ProviderStatistics.provider_name == provider_name)
    return query.order_by(desc(ProviderStatistics.date), ProviderStatistics.provider_name).all()
