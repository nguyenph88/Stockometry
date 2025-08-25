# Stockometry Missing Reports Check

The Missing Reports Check system is a simple solution for detecting missing daily reports in Stockometry. It automatically analyzes your daily report coverage and identifies any missing reports to ensure data completeness.

## 🎯 Features

- **Smart Analysis**: Automatically detects missing reports based on your configured daily schedule
- **Configurable Schedule**: Easily adjust the number of daily reports (currently 3, but configurable for future changes)
- **Excludes ONDEMAND**: Only counts scheduled reports, not manual/on-demand ones
- **Flexible Date Ranges**: Check specific date ranges or use default lookback period
- **Simple Menu Interface**: Easy-to-use numbered menu system
- **Simple & Lightweight**: Focused only on checking, no complex regeneration logic

## 🏗️ Architecture

The system consists of two key components:

### Core Components

1. **BackfillManager** - Main interface for checking missing reports
2. **ReportAnalyzer** - Analyzes existing reports to identify missing data
3. **BackfillConfig** - Configuration management for daily report schedule

### Data Flow

```
1. Query daily_reports table (exclude ONDEMAND reports)
2. Compare with expected schedule
3. Identify missing reports
4. Generate summary and coverage statistics
```

## ⚙️ Configuration

### Default Configuration

The system comes with sensible defaults:

```python
# Default daily report schedule (3 times daily)
daily_report_times = [
    time(2, 15),   # 2:15 AM UTC
    time(10, 15),  # 10:15 AM UTC  
    time(18, 15),  # 6:15 PM UTC
]

# Default settings
lookback_days = 7  # Check last 7 days
```

### Customizing Configuration

You can easily customize the configuration:

```python
from stockometry.backfill.config import BackfillConfig
from datetime import time

# Custom configuration
config = BackfillConfig(
    daily_report_times=[
        time(1, 0),    # 1:00 AM
        time(9, 0),    # 9:00 AM
        time(17, 0),   # 5:00 PM
        time(21, 0),   # 9:00 PM (4 reports per day)
    ],
    lookback_days=14  # Check last 14 days
)
```

## 🚀 Usage

### Simple Menu Interface

The system provides a user-friendly numbered menu:

```bash
python -m stockometry.backfill.cli
```

You'll see a menu like this:

```
==================================================
📊 STOCKOMETRY MISSING REPORTS CHECK
==================================================
1. Check Missing Reports
2. Get Summary
3. Show System Status
4. Exit
--------------------------------------------------
Select an option (1-4):
```

### Menu Options

#### 1. Check Missing Reports
- **Option 1**: Check for missing reports
- **Date Input**: Enter specific start/end dates or press Enter to use default lookback
- **Lookback**: If no dates specified, enter number of days to look back
- **Output**: Shows detailed results with coverage percentage and list of missing reports

#### 2. Get Summary
- **Option 2**: Get a quick summary of missing reports
- **Date Input**: Same flexible date input as option 1
- **Output**: Shows summary grouped by date with coverage statistics

#### 3. Show System Status
- **Option 3**: Display current system configuration
- **Output**: Shows daily report count, lookback days, and current schedule

#### 4. Exit
- **Option 4**: Exit the program

### Input Examples

When you select options 1 or 2, you'll be prompted for dates:

```
Enter start date (YYYY-MM-DD) or press Enter to skip: 2025-01-20
Enter end date (YYYY-MM-DD) or press Enter to skip: 2025-01-23
```

Or if you skip dates, you'll be asked for lookback days:

```
Enter number of days to look back (default: 7): 14
```

### Programmatic Usage

You can also use the system programmatically:

```python
from stockometry.backfill import BackfillManager
from stockometry.backfill.config import BackfillConfig

# Create manager with custom config
config = BackfillConfig(lookback_days=14)
manager = BackfillManager(config)

# Check missing reports
analysis = manager.check_missing_reports()

# Get summary
summary = manager.get_missing_reports_summary()
```

## 📊 Understanding Output

### Check Results

When you select option 1, you'll see:

```
📊 Check Results:
  Days checked: 7
  Reports expected: 21
  Reports found: 18
  Coverage: 85.7%

❌ Missing Reports (3):
  - 2025-01-21 at 10:15: Morning
  - 2025-01-22 at 18:15: Evening
  - 2025-01-23 at 02:15: Early Morning
```

### Summary Results

When you select option 2, you'll see:

```
📊 Summary: Found 3 missing reports
  Coverage: 85.7%

❌ Missing Reports by Date:
  2025-01-21:
    - 10:15 (Morning)
  2025-01-22:
    - 18:15 (Evening)
  2025-01-23:
    - 02:15 (Early Morning)
```

### System Status

When you select option 3, you'll see:

```
📊 System Status:
  Status: ready
  Daily reports: 3
  Lookback days: 7

📅 Current Schedule:
  1. 02:15
  2. 10:15
  3. 18:15
```

## 🔍 Important Notes

### ONDEMAND Reports Excluded

The system **only counts scheduled reports** and excludes:
- Manual reports generated via API calls
- Reports with `run_source = 'ONDEMAND'`
- Reports with `run_source = 'BACKFILL'` (generated by backfill system)
- Any other non-scheduled reports

This ensures you only see missing reports from your automated daily schedule.

### Time Windows

The system allows a 2-hour window for each scheduled report time to account for:
- Processing delays
- System load variations
- Minor timing differences

### User-Friendly Input

- **Dates**: Enter in YYYY-MM-DD format or press Enter to skip
- **Numbers**: Enter positive integers for lookback days
- **Navigation**: Use Ctrl+C to exit at any time
- **Continue**: Press Enter after each operation to return to menu

## 🛠️ Troubleshooting

### Common Issues

1. **"No reports found"**
   - Check if your database has the `daily_reports` table
   - Verify that scheduled reports are being generated
   - Check database connectivity

2. **"Unexpected coverage percentage"**
   - Verify your daily report schedule configuration
   - Check if all expected times are configured
   - Ensure lookback period is correct

3. **"Invalid date format"**
   - Use YYYY-MM-DD format (e.g., 2025-01-23)
   - Press Enter to skip and use default lookback

### Error Handling

The system gracefully handles:
- Invalid date formats
- Invalid number inputs
- Database connection issues
- Keyboard interrupts (Ctrl+C)

## 🔮 Future Enhancements

The system is designed to be easily extensible:

- **Report regeneration**: Add ability to regenerate missing reports
- **Email notifications**: Alerts when reports are missing
- **Web interface**: GUI for managing operations
- **Advanced scheduling**: Support for different schedules on different days

## 📝 Configuration Examples

### 4 Reports Per Day

```python
config = BackfillConfig(
    daily_report_times=[
        time(1, 0),    # 1:00 AM
        time(7, 0),    # 7:00 AM
        time(13, 0),   # 1:00 PM
        time(19, 0),   # 7:00 PM
    ]
)
```

### 2 Reports Per Day

```python
config = BackfillConfig(
    daily_report_times=[
        time(6, 0),    # 6:00 AM
        time(18, 0),   # 6:00 PM
    ]
)
```

### Custom Lookback Period

```python
config = BackfillConfig(
    lookback_days=30  # Check last 30 days
)
```

## 🤝 Contributing

The system is designed to be modular and extensible. Key areas for contribution:

- Additional validation rules
- Enhanced scheduling algorithms
- Performance optimizations
- Additional menu options

## 📚 API Reference

For detailed API documentation, see the individual module docstrings:

- `BackfillManager`: Main interface for checking missing reports
- `ReportAnalyzer`: Report analysis and missing data detection
- `BackfillConfig`: Configuration management
- `cli`: Simple menu interface
