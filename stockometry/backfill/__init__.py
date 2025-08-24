"""
Backfill Package for Stockometry

This package handles checking for missing daily reports.
It looks back 7 days (today + last 6 days) and identifies any missing reports
based on the configured daily report schedule. It excludes ONDEMAND reports.
"""

from .backfill_manager import BackfillManager
from .report_analyzer import ReportAnalyzer

__all__ = [
    'BackfillManager',
    'ReportAnalyzer'
]
