"""
Stockometry FastAPI Routes
Basic API endpoints for FastAPI integration.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Optional, List
from datetime import date
from ..core import run_stockometry_analysis
from ..core.analysis.today_analyzer import analyze_todays_impact
from ..core.analysis.historical_analyzer import analyze_historical_trends
from ..core.output.processor import OutputProcessor
from ..database import get_db_connection
from ..config import settings

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

@router.get("/reports/{report_id}/full")
async def get_full_report(report_id: int):
    """
    Get complete Stockometry report with all signals and analysis details
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get report metadata
                cursor.execute("""
                    SELECT id, report_date, executive_summary, run_source, generated_at_utc
                    FROM daily_reports 
                    WHERE id = %s
                """, (report_id,))
                report_row = cursor.fetchone()
                
                if not report_row:
                    raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
                
                report_id, report_date, executive_summary, run_source, generated_at_utc = report_row
                
                # Get signals for this report
                cursor.execute("""
                    SELECT id, signal_type, sector, direction, confidence, details, source_articles
                    FROM report_signals 
                    WHERE report_id = %s
                    ORDER BY confidence DESC
                """, (report_id,))
                signal_rows = cursor.fetchall()
                
                signals = []
                for signal_row in signal_rows:
                    signal_id, signal_type, sector, direction, confidence, details, source_articles = signal_row
                    signals.append({
                        "signal_id": signal_id,
                        "type": signal_type,
                        "sector": sector,
                        "direction": direction,
                        "confidence": confidence,
                        "details": details,
                        "source_articles": source_articles or []
                    })
                
                return {
                    "report_id": report_id,
                    "report_date": str(report_date),
                    "executive_summary": executive_summary,
                    "run_source": run_source,
                    "generated_at_utc": generated_at_utc.isoformat(),
                    "signals": signals,
                    "total_signals": len(signals)
                }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch full report: {str(e)}")

@router.get("/signals/{report_id}")
async def get_report_signals(report_id: int):
    """
    Get individual trading signals for a specific report
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, signal_type, sector, direction, confidence, details, source_articles
                    FROM report_signals 
                    WHERE report_id = %s
                    ORDER BY confidence DESC
                """, (report_id,))
                rows = cursor.fetchall()
                
                if not rows:
                    raise HTTPException(status_code=404, detail=f"No signals found for report {report_id}")
                
                signals = []
                for row in rows:
                    signal_id, signal_type, sector, direction, confidence, details, source_articles = row
                    signals.append({
                        "signal_id": signal_id,
                        "type": signal_type,
                        "sector": sector,
                        "direction": direction,
                        "confidence": confidence,
                        "details": details,
                        "source_articles": source_articles or []
                    })
                
                return {"signals": signals, "count": len(signals)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch signals: {str(e)}")

@router.get("/export/{report_id}/json")
async def export_report_json(report_id: int):
    """
    Export a report as JSON format
    """
    try:
        output_processor = OutputProcessor(run_source="ONDEMAND")
        report_data = output_processor.export_to_json(report_id=report_id)
        
        if not report_data:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found or no data available")
        
        return report_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")

@router.get("/analyze/today")
async def get_todays_analysis():
    """
    Get today's high-impact news analysis (independent of full reports)
    """
    try:
        analysis_result = analyze_todays_impact()
        return {
            "analysis_date": str(date.today()),
            "signals": analysis_result.get("signals", []),
            "summary_points": analysis_result.get("summary_points", []),
            "total_signals": len(analysis_result.get("signals", [])),
            "run_source": "ONDEMAND"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze today's news: {str(e)}")

@router.get("/analyze/historical")
async def get_historical_analysis(days: int = 6):
    """
    Get historical trends analysis for the specified number of days
    """
    try:
        analysis_result = analyze_historical_trends(days)
        return {
            "analysis_period_days": days,
            "signals": analysis_result.get("signals", []),
            "summary_points": analysis_result.get("summary_points", []),
            "total_signals": len(analysis_result.get("signals", [])),
            "run_source": "ONDEMAND"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze historical trends: {str(e)}")

@router.get("/config")
async def get_configuration():
    """
    Get current Stockometry configuration (non-sensitive)
    """
    try:
        return {
            "environment": settings.environment,
            "database": {
                "host": settings.database.get("host"),
                "port": settings.database.get("port"),
                "database": settings.database.get("database"),
                "active_database": settings.db_name_active
            },
            "market_data": {
                "tickers_count": len(settings.market_data.get("tickers", [])),
                "period": settings.market_data.get("period")
            },
            "scheduler": {
                "timezone": settings.scheduler.get("timezone"),
                "news_interval_hours": settings.scheduler.get("news_interval_hours"),
                "market_data_hour": settings.scheduler.get("market_data_hour"),
                "nlp_interval_minutes": settings.scheduler.get("nlp_interval_minutes"),
                "final_report_hour": settings.scheduler.get("final_report_hour")
            },
            "analysis": {
                "historical_days": settings.analysis.get("historical_days"),
                "extreme_sentiment_threshold": settings.analysis.get("extreme_sentiment_threshold")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch configuration: {str(e)}")

@router.post("/scheduler/start")
async def start_scheduler():
    """
    Start the Stockometry scheduler
    """
    try:
        from ..scheduler.scheduler import start_scheduler as start_sched
        start_sched()
        return {
            "message": "Scheduler started successfully",
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/scheduler/stop")
async def stop_scheduler():
    """
    Stop the Stockometry scheduler
    """
    try:
        from ..scheduler.scheduler import stop_scheduler as stop_sched
        stop_sched()
        return {
            "message": "Scheduler stopped successfully",
            "status": "stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@router.get("/scheduler/status")
async def get_scheduler_status():
    """
    Get current scheduler status
    """
    try:
        from ..scheduler.scheduler import get_scheduler_status as get_sched_status
        status = get_sched_status()
        return status
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e)
        }

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
