"""
Stockometry Tests - Test suite for the modular package
"""

# Import all test modules for easy access
from .test_setup import *
from .test_e2e import *
from .test_e2e_bullish_tech import *
from .test_e2e_bearish_financial import *
from .test_e2e_mixed_signals import *
from .test_e2e_edge_cases import *
from .run_all_e2e_tests import *

__all__ = [
    # Shared test setup and utilities
    "test_setup",
    "E2ETestSetup",
    "TestDataGenerator", 
    "TestVerification",
    # Individual test modules
    "test_collectors",
    "test_database",
    "test_milestone2_NLP",
    "test_e2e",
    "test_e2e_bullish_tech",
    "test_e2e_bearish_financial",
    "test_e2e_mixed_signals",
    "test_e2e_edge_cases",
    "run_all_e2e_tests"
]
