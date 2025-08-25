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
                time(6, 0),    # 6:00 AM UTC - US pre-market, European morning
                time(14, 0),   # 2:00 PM UTC - US morning trading, European midday
                time(22, 0),   # 10:00 PM UTC - US market close, complete daily coverage
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
