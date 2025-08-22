"""
Stockometry FastAPI Routes
Basic API endpoints for FastAPI integration.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Optional, List
from datetime import date
from ..core import run_stockometry_analysis
from ..database import get_db_connection

# Create the router at module level
router = APIRouter(prefix="/stockometry", tags=["stockometry"])

@router.post("/analyze")
async def trigger_analysis(background_tasks: BackgroundTasks):
    """
    Trigger a manual Stockometry analysis
    """
    try:
        background_tasks.add_task(run_stockometry_analysis, "ONDEMAND")
        return {
            "message": "Analysis started",
            "status": "running",
            "run_source": "ONDEMAND"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@router.get("/reports/latest")
async def get_latest_report():
    """
    Get the latest Stockometry report
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, report_date, executive_summary, run_source, generated_at_utc
                    FROM daily_reports 
                    ORDER BY generated_at_utc DESC 
                    LIMIT 1
                """)
                row = cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="No reports found")
                
                report_id, report_date, executive_summary, run_source, generated_at_utc = row
                
                return {
                    "report_id": report_id,
                    "report_date": str(report_date),
                    "executive_summary": executive_summary,
                    "run_source": run_source,
                    "generated_at_utc": generated_at_utc.isoformat()
                }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch report: {str(e)}")

@router.get("/reports/{report_date}")
async def get_report_by_date(report_date: str):
    """
    Get Stockometry report for a specific date (YYYY-MM-DD)
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, report_date, executive_summary, run_source, generated_at_utc
                    FROM daily_reports 
                    WHERE report_date = %s
                """, (report_date,))
                row = cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail=f"No report found for date: {report_date}")
                
                report_id, report_date, executive_summary, run_source, generated_at_utc = row
                
                return {
                    "report_id": report_id,
                    "report_date": str(report_date),
                    "executive_summary": executive_summary,
                    "run_source": run_source,
                    "generated_at_utc": generated_at_utc.isoformat()
                }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch report: {str(e)}")

@router.get("/reports")
async def list_reports(limit: int = 10):
    """
    List recent Stockometry reports
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, report_date, executive_summary, run_source, generated_at_utc
                    FROM daily_reports 
                    ORDER BY generated_at_utc DESC 
                    LIMIT %s
                """, (limit,))
                rows = cursor.fetchall()
                
                reports = []
                for row in rows:
                    report_id, report_date, executive_summary, run_source, generated_at_utc = row
                    reports.append({
                        "report_id": report_id,
                        "report_date": str(report_date),
                        "executive_summary": executive_summary,
                        "run_source": run_source,
                        "generated_at_utc": generated_at_utc.isoformat()
                    })
                
                return {"reports": reports, "count": len(reports)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {str(e)}")

@router.get("/status")
async def get_status():
    """
    Get Stockometry service status
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM daily_reports")
                report_count = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT generated_at_utc 
                    FROM daily_reports 
                    ORDER BY generated_at_utc DESC 
                    LIMIT 1
                """)
                latest_report = cursor.fetchone()
                
                return {
                    "status": "healthy",
                    "total_reports": report_count,
                    "latest_report": latest_report[0].isoformat() if latest_report else None,
                    "version": "3.0.0"
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "version": "3.0.0"
        }

# Keep the create_router function for backward compatibility
def create_router() -> APIRouter:
    """Create and configure the Stockometry API router (backward compatibility)"""
    return router
