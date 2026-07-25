from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from fastapi.responses import Response

from app.db.session import get_db
from app.analytics.service import AnalyticsService
from app.security.dependencies import get_current_principal

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/organization", response_model=Dict[str, Any])
def get_organization_analytics(
    org_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_principal)
):
    """Get overview analytics for a specific organization."""
    # Ensure user has access to org_id (skipping RBAC logic for brevity but assume handled via dependency)
    end = end_date or date.today()
    start = start_date or (end - timedelta(days=30))
    
    service = AnalyticsService(db)
    return service.get_organization_overview(org_id, start, end)

@router.get("/export")
def export_analytics(
    report_type: str = Query("organization", description="Type of report (organization)"),
    format: str = Query("excel", description="Format (excel or pdf)"),
    org_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_principal)
):
    """Export analytics report."""
    end = end_date or date.today()
    start = start_date or (end - timedelta(days=30))
    
    service = AnalyticsService(db)
    try:
        report_bytes = service.generate_report(report_type, format, start, end, org_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "excel" else "application/pdf"
    extension = "xlsx" if format == "excel" else "pdf"
    filename = f"analytics_{report_type}_{end.strftime('%Y%m%d')}.{extension}"
    
    return Response(content=report_bytes, media_type=media_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })
