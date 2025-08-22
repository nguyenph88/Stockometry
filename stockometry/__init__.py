"""
Stockometry - Market Analysis Tool
A modular package for market data analysis and signal generation.
"""

__version__ = "3.0.0"
__author__ = "Stockometry Team"

# Core functionality
from .core import run_stockometry_analysis

# CLI functionality (for standalone mode)
from .cli import run_once, start_scheduler

# API functionality (for FastAPI integration)
from .api import create_router

# Test functionality (for testing)
from .tests import test_e2e, test_e2e_bullish_tech, test_e2e_bearish_financial, test_e2e_mixed_signals, test_e2e_edge_cases, run_all_e2e_tests

__all__ = [
    "run_stockometry_analysis",
    "run_once", 
    "start_scheduler",
    "create_router",
    "test_e2e",
    "test_e2e_bullish_tech",
    "test_e2e_bearish_financial", 
    "test_e2e_mixed_signals",
    "test_e2e_edge_cases",
    "run_all_e2e_tests"
]
