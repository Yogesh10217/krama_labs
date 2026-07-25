from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models.analytics import CostStatistics

def get_cost_statistics(db: Session, start_date: date, end_date: date, org_id: Optional[str] = None, provider_name: Optional[str] = None) -> List[CostStatistics]:
    """Retrieve cost statistics for a given date range, optionally filtered by org or provider."""
    query = db.query(CostStatistics).filter(
        CostStatistics.date >= start_date,
        CostStatistics.date <= end_date
    )
    if org_id:
        query = query.filter(CostStatistics.organization_id == org_id)
    if provider_name:
        query = query.filter(CostStatistics.provider_name == provider_name)
        
    return query.order_by(desc(CostStatistics.date)).all()
