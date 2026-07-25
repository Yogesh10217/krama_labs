from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from fastapi.responses import Response

from app.db.session import get_db
from app.analytics.service import AnalyticsService
from app.security.dependencies import get_current_principal

router = APIRouter(prefix="/admin/analytics", tags=["admin", "analytics"])

# In a real app, Depends(get_current_principal) should be combined with RBAC (is_system_admin)

@router.get("/system", response_model=Dict[str, Any])
def get_system_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_principal)
):
    """Get system-wide overview analytics."""
    end = end_date or date.today()
    start = start_date or (end - timedelta(days=30))
    
    service = AnalyticsService(db)
    return service.get_system_overview(start, end)

@router.get("/providers", response_model=Dict[str, Any])
def get_provider_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_principal)
):
    """Get provider analytics."""
    end = end_date or date.today()
    start = start_date or (end - timedelta(days=30))
    
    service = AnalyticsService(db)
    return service.get_provider_overview(start, end)

@router.get("/export")
def export_system_analytics(
    report_type: str = Query(..., description="Type of report (system or provider)"),
    format: str = Query("excel", description="Format (excel or pdf)"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_principal)
):
    """Export system analytics report."""
    end = end_date or date.today()
    start = start_date or (end - timedelta(days=30))
    
    service = AnalyticsService(db)
    try:
        report_bytes = service.generate_report(report_type, format, start, end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "excel" else "application/pdf"
    extension = "xlsx" if format == "excel" else "pdf"
    filename = f"admin_analytics_{report_type}_{end.strftime('%Y%m%d')}.{extension}"
    
    return Response(content=report_bytes, media_type=media_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })
