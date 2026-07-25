from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.analytics.statistics import get_daily_statistics, get_organization_statistics
from app.analytics.provider_metrics import get_provider_statistics
from app.analytics.sla import get_sla_statistics
from app.analytics.cost import get_cost_statistics
from app.analytics.exports import generate_excel_report, generate_pdf_report

class AnalyticsService:
    """Facade for analytics queries and report generation."""

    def __init__(self, db: Session):
        self.db = db

    def get_system_overview(self, start_date: date, end_date: date) -> Dict[str, Any]:
        daily = get_daily_statistics(self.db, start_date, end_date)
        sla = get_sla_statistics(self.db, start_date, end_date)
        return {
            "daily_statistics": [d.__dict__ for d in daily],
            "sla_statistics": [s.__dict__ for s in sla]
        }

    def get_organization_overview(self, org_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        org_stats = get_organization_statistics(self.db, org_id, start_date, end_date)
        cost_stats = get_cost_statistics(self.db, start_date, end_date, org_id=org_id)
        return {
            "organization_statistics": [o.__dict__ for o in org_stats],
            "cost_statistics": [c.__dict__ for c in cost_stats]
        }
        
    def get_provider_overview(self, start_date: date, end_date: date) -> Dict[str, Any]:
        prov_stats = get_provider_statistics(self.db, start_date, end_date)
        cost_stats = get_cost_statistics(self.db, start_date, end_date)
        return {
            "provider_statistics": [p.__dict__ for p in prov_stats],
            "cost_statistics": [c.__dict__ for c in cost_stats]
        }

    def generate_report(self, report_type: str, format: str, start_date: date, end_date: date, org_id: Optional[str] = None) -> bytes:
        if report_type == "system":
            data = self.get_system_overview(start_date, end_date)
        elif report_type == "organization":
            if not org_id:
                raise ValueError("org_id is required for organization report")
            data = self.get_organization_overview(org_id, start_date, end_date)
        elif report_type == "provider":
            data = self.get_provider_overview(start_date, end_date)
        else:
            raise ValueError("Invalid report type")

        if format == "excel":
            return generate_excel_report(data, report_type)
        elif format == "pdf":
            return generate_pdf_report(data, report_type)
        else:
            raise ValueError("Invalid format")
