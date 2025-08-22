"""
Stockometry - A two-stage financial analysis system for market sentiment and trading signals.

This package provides:
- Core analysis functionality
- CLI tools for standalone operation
- FastAPI integration
- Database management
- Scheduled analysis
- Utility functions
- Comprehensive documentation
"""

__version__ = "3.0.0"
__author__ = "Stockometry Team"

# Core functionality
from .core import run_stockometry_analysis

# CLI tools
from .cli import run_analysis_and_save, start_scheduler

# API integration
from .api import router as api_router

# Database utilities
from .database import get_db_connection, get_db_connection_string, init_db

# Scheduler functionality (separate from CLI scheduler)
from .scheduler.scheduler import main as run_scheduler, run_synthesis_and_save

# Utility functions
from .utils.export_reports import (
    export_latest_report,
    export_report_by_date,
    export_report_by_id,
    list_available_reports
)

from .utils.get_individual_reports import fetch_independent_analyses

# Test modules
from .tests import (
    test_setup,
    test_e2e,
    test_e2e_bullish_tech,
    test_e2e_bearish_financial,
    test_e2e_mixed_signals,
    test_e2e_edge_cases,
    run_all_e2e_tests
)

__all__ = [
    # Core
    'run_stockometry_analysis',
    
    # CLI
    'run_analysis_and_save',
    'start_scheduler',
    
    # API
    'api_router',
    
    # Database
    'get_db_connection',
    'get_db_connection_string',
    'init_db',
    
    # Scheduler
    'run_scheduler',
    'run_synthesis_and_save',
    
    # Utilities
    'export_latest_report',
    'export_report_by_date',
    'export_report_by_id',
    'list_available_reports',
    'fetch_independent_analyses',
    
    # Tests
    'test_setup',
    'test_e2e',
    'test_e2e_bullish_tech',
    'test_e2e_bearish_financial',
    'test_e2e_mixed_signals',
    'test_e2e_edge_cases',
    'run_all_e2e_tests'
]
