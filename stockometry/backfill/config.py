"""
Configuration for the Backfill system

This module contains configuration options for checking missing daily reports.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import time

@dataclass
class BackfillConfig:
    """Configuration for the backfill system"""
    
    # Daily report schedule configuration
    daily_report_times: List[time] = None
    
    # Lookback period (how many days to check)
    lookback_days: int = 7
    
    def __post_init__(self):
        """Set default daily report times if none provided"""
        if self.daily_report_times is None:
            # Default to current 3-times daily schedule
            self.daily_report_times = [
                time(2, 15),   # 2:15 AM UTC
                time(10, 15),  # 10:15 AM UTC  
                time(18, 15),  # 6:15 PM UTC
            ]
    
    @property
    def daily_report_count(self) -> int:
        """Get the total number of reports expected per day"""
        return len(self.daily_report_times)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for storage/display"""
        return {
            "daily_report_times": [t.strftime("%H:%M") for t in self.daily_report_times],
            "daily_report_count": self.daily_report_count,
            "lookback_days": self.lookback_days
        }

# Default configuration instance
DEFAULT_BACKFILL_CONFIG = BackfillConfig()
