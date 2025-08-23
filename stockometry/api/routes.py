"""
Stockometry FastAPI Routes
Basic API endpoints for FastAPI integration.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Path
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field
from ..core import run_stockometry_analysis
from ..core.analysis.today_analyzer import analyze_todays_impact
from ..core.analysis.historical_analyzer import analyze_historical_trends
from ..core.output.processor import OutputProcessor
from ..database import get_db_connection
from ..config import settings
from ..scheduler.scheduler import start_scheduler as start_sched, stop_scheduler as stop_sched, get_scheduler_status as get_sched_status

# Create the router at module level
router = APIRouter(prefix="/stockometry", tags=["stockometry"])

# --- Response Models ---
class AnalysisResponse(BaseModel):
    message: str
    status: str
    run_source: str

class ReportBase(BaseModel):
    report_id: int
    report_date: str
    executive_summary: str
    run_source: str
    generated_at_utc: str

class ReportListResponse(BaseModel):
    reports: List[ReportBase]
    count: int

class SignalBase(BaseModel):
    signal_id: int
    type: str
    sector: str
    direction: str
    details: str
    stock_symbol: str = ""

class FullReportResponse(BaseModel):
    report_id: int
    report_date: str
    executive_summary: str
    run_source: str
    generated_at_utc: str
    signals: List[SignalBase]
    total_signals: int

class SignalListResponse(BaseModel):
    signals: List[SignalBase]
    count: int

class TodayAnalysisResponse(BaseModel):
    analysis_date: str
    signals: List[dict]
    summary_points: List[str]
    total_signals: int
    run_source: str

class HistoricalAnalysisResponse(BaseModel):
    analysis_period_days: int
    signals: List[dict]
    summary_points: List[str]
    total_signals: int
    run_source: str

class ConfigResponse(BaseModel):
    environment: str
    database: dict
    market_data: dict
    scheduler: dict
    analysis: dict

class SchedulerResponse(BaseModel):
    message: str
    status: str

class StatusResponse(BaseModel):
    status: str
    total_reports: Optional[int] = None
    latest_report: Optional[str] = None
    version: str
    error: Optional[str] = None

@router.post("/analyze", response_model=AnalysisResponse)
async def trigger_analysis(background_tasks: BackgroundTasks):
    """
    Trigger a manual Stockometry analysis
    """
    try:
        background_tasks.add_task(run_stockometry_analysis, "ONDEMAND")
        return AnalysisResponse(
            message="Analysis started",
            status="running",
            run_source="ONDEMAND"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@router.get("/reports/latest", response_model=FullReportResponse)
async def get_latest_report():
    """
    Get the latest Stockometry report with full details and signals
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get latest report metadata
                cursor.execute("""
                    SELECT id, report_date, executive_summary, run_source, generated_at_utc
                    FROM daily_reports 
                    ORDER BY generated_at_utc DESC 
                    LIMIT 1
                """)
                report_row = cursor.fetchone()
                
                if not report_row:
                    raise HTTPException(status_code=404, detail="No reports found")
                
                report_id, report_date, executive_summary, run_source, generated_at_utc = report_row
                
                # Get signals for this report
                cursor.execute("""
                    SELECT id, signal_type, sector, direction, details, stock_symbol
                    FROM report_signals 
                    WHERE report_id = %s
                    ORDER BY id DESC
                """, (report_id,))
                signal_rows = cursor.fetchall()
                
                signals = []
                for signal_row in signal_rows:
                    signal_id, signal_type, sector, direction, details, stock_symbol = signal_row
                    signals.append(SignalBase(
                        signal_id=signal_id,
                        type=signal_type,
                        sector=sector,
                        direction=direction,
                        details=details,
                        stock_symbol=stock_symbol or ""
                    ))
                
                return FullReportResponse(
                    report_id=report_id,
                    report_date=str(report_date),
                    executive_summary=executive_summary,
                    run_source=run_source,
                    generated_at_utc=generated_at_utc.isoformat(),
                    signals=signals,
                    total_signals=len(signals)
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch latest report: {str(e)}")

@router.get("/reports/by-date/{report_date}", response_model=ReportBase)
async def get_report_by_date(
    report_date: str = Path(..., description="Report date in YYYY-MM-DD format", regex=r"^\d{4}-\d{2}-\d{2}$")
):
    """
    Get Stockometry report for a specific date (YYYY-MM-DD)
    """
    try:
        # Validate date format
        datetime.strptime(report_date, "%Y-%m-%d")
        
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
                
                return ReportBase(
                    report_id=report_id,
                    report_date=str(report_date),
                    executive_summary=executive_summary,
                    run_source=run_source,
                    generated_at_utc=generated_at_utc.isoformat()
                )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch report: {str(e)}")

@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    limit: int = Query(10, ge=1, le=100, description="Number of reports to return (1-100)")
):
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
                    reports.append(ReportBase(
                        report_id=report_id,
                        report_date=str(report_date),
                        executive_summary=executive_summary,
                        run_source=run_source,
                        generated_at_utc=generated_at_utc.isoformat()
                    ))
                
                return ReportListResponse(reports=reports, count=len(reports))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {str(e)}")

@router.get("/reports/{report_id}/full", response_model=FullReportResponse)
async def get_full_report(
    report_id: int = Path(..., ge=1, description="Report ID")
):
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
                    SELECT id, signal_type, sector, direction, details, stock_symbol
                    FROM report_signals 
                    WHERE report_id = %s
                    ORDER BY id DESC
                """, (report_id,))
                signal_rows = cursor.fetchall()
                
                signals = []
                for signal_row in signal_rows:
                    signal_id, signal_type, sector, direction, details, stock_symbol = signal_row
                    signals.append(SignalBase(
                        signal_id=signal_id,
                        type=signal_type,
                        sector=sector,
                        direction=direction,
                        details=details,
                        stock_symbol=stock_symbol or ""
                    ))
                
                return FullReportResponse(
                    report_id=report_id,
                    report_date=str(report_date),
                    executive_summary=executive_summary,
                    run_source=run_source,
                    generated_at_utc=generated_at_utc.isoformat(),
                    signals=signals,
                    total_signals=len(signals)
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch full report: {str(e)}")

@router.get("/signals/{report_id}", response_model=SignalListResponse)
async def get_report_signals(
    report_id: int = Path(..., ge=1, description="Report ID")
):
    """
    Get individual trading signals for a specific report
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, signal_type, sector, direction, details, stock_symbol
                    FROM report_signals 
                    WHERE report_id = %s
                    ORDER BY id DESC
                """, (report_id,))
                rows = cursor.fetchall()
                
                if not rows:
                    raise HTTPException(status_code=404, detail=f"No signals found for report {report_id}")
                
                signals = []
                for row in rows:
                    signal_id, signal_type, sector, direction, details, stock_symbol = row
                    signals.append(SignalBase(
                        signal_id=signal_id,
                        type=signal_type,
                        sector=sector,
                        direction=direction,
                        details=details,
                        stock_symbol=stock_symbol or ""
                    ))
                
                return SignalListResponse(signals=signals, count=len(signals))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch signals: {str(e)}")

@router.get("/export/{report_id}/json")
async def export_report_json(
    report_id: int = Path(..., ge=1, description="Report ID")
):
    """
    Export a report as JSON format
    """
    try:
        output_processor = OutputProcessor({}, run_source="ONDEMAND")
        report_data = output_processor.export_to_json(report_id=report_id)
        
        if not report_data:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found or no data available")
        
        return report_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")

@router.get("/analyze/today", response_model=TodayAnalysisResponse)
async def get_todays_analysis():
    """
    Get today's high-impact news analysis (independent of full reports)
    """
    try:
        analysis_result = analyze_todays_impact()
        return TodayAnalysisResponse(
            analysis_date=str(date.today()),
            signals=analysis_result.get("signals", []),
            summary_points=analysis_result.get("summary_points", []),
            total_signals=len(analysis_result.get("signals", [])),
            run_source="ONDEMAND"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze today's news: {str(e)}")

@router.get("/analyze/historical", response_model=HistoricalAnalysisResponse)
async def get_historical_analysis(
    days: int = Query(6, ge=1, le=30, description="Number of days to analyze (1-30)")
):
    """
    Get historical trends analysis for the specified number of days
    """
    try:
        analysis_result = analyze_historical_trends(days)
        return HistoricalAnalysisResponse(
            analysis_period_days=days,
            signals=analysis_result.get("signals", []),
            summary_points=analysis_result.get("summary_points", []),
            total_signals=len(analysis_result.get("signals", [])),
            run_source="ONDEMAND"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze historical trends: {str(e)}")

@router.get("/config", response_model=ConfigResponse)
async def get_configuration():
    """
    Get current Stockometry configuration (non-sensitive)
    """
    try:
        return ConfigResponse(
            environment=settings.environment,
            database={
                "host": settings.db_host,
                "port": settings.db_port,
                "name": settings.db_name,
                "active_database": settings.db_name_active
            },
            market_data={
                "tickers_count": len(settings.market_data.get("tickers", [])),
                "period": settings.market_data.get("period")
            },
            scheduler={
                "timezone": settings.scheduler_timezone,
                "news_interval_hours": settings.scheduler_news_interval_hours,
                "market_data_hour": settings.scheduler_market_data_hour,
                "nlp_interval_minutes": settings.scheduler_nlp_interval_minutes,
                "final_report_hour": settings.scheduler_final_report_hour
            },
            analysis={
                "historical_days": settings.analysis_historical_days,
                "extreme_sentiment_threshold": settings.analysis_extreme_sentiment_threshold
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch configuration: {str(e)}")

@router.post("/scheduler/start", response_model=SchedulerResponse)
async def start_scheduler():
    """
    Start the Stockometry scheduler
    """
    try:
        start_sched()
        return SchedulerResponse(
            message="Scheduler started successfully",
            status="running"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/scheduler/stop", response_model=SchedulerResponse)
async def stop_scheduler():
    """
    Stop the Stockometry scheduler
    """
    try:
        stop_sched()
        return SchedulerResponse(
            message="Scheduler stopped successfully",
            status="stopped"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@router.get("/scheduler/status")
async def get_scheduler_status():
    """
    Get current scheduler status
    """
    try:
        status = get_sched_status()
        return status
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e)
        }

@router.get("/health", response_model=StatusResponse)
async def health():
    """
    Health check endpoint - Get Stockometry service health status
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
                
                return StatusResponse(
                    status="healthy",
                    total_reports=report_count,
                    latest_report=latest_report[0].isoformat() if latest_report else None,
                    version="2.0.0"
                )
    except Exception as e:
        return StatusResponse(
            status="unhealthy",
            error=str(e),
            version="2.0.0"
        )

# Keep the create_router function for backward compatibility
def create_router() -> APIRouter:
    """Create and configure the Stockometry API router (backward compatibility)"""
    return router
