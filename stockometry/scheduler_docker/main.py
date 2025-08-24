"""
FastAPI application for Scheduler Docker Service

This FastAPI app runs the Docker scheduler and provides endpoints
to control it. It's designed to run in a separate container.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import signal
import sys
from typing import Dict, Any

from .scheduler_docker import SchedulerDocker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler_docker = SchedulerDocker()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Starting Stockometry Scheduler Docker Service...")
    try:
        # Auto-start the scheduler on container startup
        result = scheduler_docker.start()
        if result["status"] == "started":
            logger.info("Scheduler Docker auto-started successfully")
        else:
            logger.warning(f"Scheduler Docker auto-start result: {result}")
    except Exception as e:
        logger.error(f"Failed to auto-start Scheduler Docker: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Stockometry Scheduler Docker Service...")
    try:
        scheduler_docker.stop()
        logger.info("Scheduler Docker stopped gracefully")
    except Exception as e:
        logger.error(f"Error during Scheduler Docker shutdown: {str(e)}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Stockometry Scheduler Docker",
    description="Docker-optimized scheduler service for Stockometry",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for Docker container communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for your Docker setup
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Signal handlers for graceful shutdown in Docker
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    scheduler_docker.stop()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint - service information"""
    return {
        "service": "Stockometry Scheduler Docker",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "start": "/start",
            "stop": "/stop",
            "restart": "/restart",
            "status": "/status",
            "health": "/health"
        }
    }

@app.post("/start")
async def start_scheduler():
    """Start the Docker scheduler"""
    try:
        result = scheduler_docker.start()
        if result["status"] == "started":
            return JSONResponse(
                status_code=200,
                content=result
            )
        elif result["status"] == "already_running":
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@app.post("/stop")
async def stop_scheduler():
    """Stop the Docker scheduler"""
    try:
        result = scheduler_docker.stop()
        if result["status"] in ["stopped", "not_running"]:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@app.post("/restart")
async def restart_scheduler():
    """Restart the Docker scheduler"""
    try:
        result = scheduler_docker.restart()
        if result["status"] == "started":
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        logger.error(f"Error restarting scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to restart scheduler: {str(e)}")

@app.get("/status")
async def get_scheduler_status():
    """Get the current status of the Docker scheduler"""
    try:
        status = scheduler_docker.get_status()
        return JSONResponse(
            status_code=200,
            content=status
        )
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker container monitoring"""
    try:
        is_running = scheduler_docker.is_running()
        return {
            "status": "healthy" if is_running else "unhealthy",
            "scheduler_running": is_running,
            "service": "Stockometry Scheduler Docker"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "Stockometry Scheduler Docker"
        }

@app.get("/jobs")
async def get_scheduler_jobs():
    """Get detailed information about all scheduled jobs"""
    try:
        status = scheduler_docker.get_status()
        if status.get("running"):
            return JSONResponse(
                status_code=200,
                content={
                    "jobs": status.get("jobs", []),
                    "total_jobs": status.get("total_jobs", 0)
                }
            )
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "jobs": [],
                    "total_jobs": 0,
                    "message": "Scheduler is not running"
                }
            )
    except Exception as e:
        logger.error(f"Error getting scheduler jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler jobs: {str(e)}")

if __name__ == "__main__":
    """Run the FastAPI application"""
    logger.info("Starting Stockometry Scheduler Docker Service...")
    
    # Run with uvicorn
    uvicorn.run(
        "stockometry.scheduler_docker.main:app",
        host="0.0.0.0",  # Bind to all interfaces for Docker
        port=8005,  # Changed from 8001 to 8005
        reload=False,  # Disable reload in production Docker
        log_level="info"
    )
