"""
FastAPI App Template for Stockometry Integration

This example shows how to integrate Stockometry into an existing FastAPI application.
Copy this file to your FastAPI project and modify as needed.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Import Stockometry components
from stockometry.api import router as stockometry_router
from stockometry.database import init_db
from stockometry.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Stockometry FastAPI application...")
    print(f"📊 Environment: {settings.environment}")
    print(f"🗄️  Database: {settings.db_name_active}")
    
    # Initialize database
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Stockometry FastAPI application...")

# Create FastAPI app
app = FastAPI(
    title="Stockometry API",
    description="Financial market sentiment analysis and trading signals",
    version="3.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Stockometry router
app.include_router(stockometry_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Stockometry API",
        "version": "3.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "stockometry_endpoints": "/stockometry"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Stockometry FastAPI",
        "version": "3.0.0"
    }

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
