# rune_once.py - Independent Stockometry Runner

## Overview

`rune_once.py` is a **completely independent** script that runs the complete Stockometry pipeline once without any scheduler dependencies. It's designed for:

- **Manual production runs** when you want fresh data and analysis
- **Testing** the complete pipeline independently
- **Scheduled runs** via external schedulers (cron, Windows Task Scheduler, etc.)
- **Development and debugging** without the full scheduler

## Key Features

✅ **Completely Independent** - No scheduler dependencies  
✅ **Real API Calls** - Fetches fresh data from NewsAPI and yfinance  
✅ **Production Database** - Saves to production database (not staging)  
✅ **Comprehensive Logging** - Detailed logs in `rune_once.log`  
✅ **Error Handling** - Robust error handling and reporting  
✅ **Progress Tracking** - Clear step-by-step progress indicators  

## What It Does

The script runs the complete Stockometry pipeline in 5 steps:

1. **📊 Initialize Production Database** - Ensures database is ready
2. **📰 Fetch Fresh News** - Gets latest news from NewsAPI
3. **📈 Fetch Market Data** - Gets latest market data from yfinance
4. **🧠 Process with NLP** - Analyzes articles with advanced NLP
5. **🔍 Run Analysis & Save** - Generates report and saves to production DB

## Usage

### Basic Run
```bash
python src/rune_once.py
```

### With Python Module
```bash
python -m src.rune_once
```

### Import in Another Script
```python
from src.rune_once import run_job_now

# Run the complete pipeline
success = run_job_now()
if success:
    print("Pipeline completed successfully!")
```

## Output

### Console Output
```
🎯 STOCKOMETRY INDEPENDENT PRODUCTION RUN
============================================================
📋 This script runs completely independently
📋 No scheduler or external dependencies required
📋 Fetches real data from APIs and saves to production DB
============================================================

🚀 Starting Stockometry Production Run (Independent Mode)
📊 [STEP 1/5] Initializing production database...
✅ Database initialized successfully
📰 [STEP 2/5] Fetching fresh news from NewsAPI...
✅ News collection completed
📈 [STEP 3/5] Fetching fresh market data from yfinance...
✅ Market data collection completed
🧠 [STEP 4/5] Processing articles with NLP...
✅ NLP processing completed
🔍 [STEP 5/5] Running analysis and saving to production database...
✅ Analysis and database save completed
🎉 Production run completed successfully in 45.23 seconds
📁 Check the 'output/' directory for the generated JSON report
```

### Log File
Detailed logs are saved to `rune_once.log` with timestamps and log levels.

### Generated Files
- **JSON Report**: `output/report_YYYY-MM-DD_HHMMSS_ondemand.json` (includes time and run source)
- **Database**: Results saved to production database
- **Log File**: `rune_once.log` with detailed execution logs

## Configuration

### Environment Variables (.env)
```bash
# Database Configuration (Production)
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=stockometry_production

# API Keys
NEWS_API_KEY=your_news_api_key
```

### Settings File (settings.yml)
```yaml
news_api:
  base_url: "https://newsapi.org/v2/everything"
  query_params:
    q: "stock market OR finance OR economy"
    language: "en"
    sortBy: "publishedAt"

market_data:
  tickers: ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
  period: "1mo"
```

## Error Handling

The script includes comprehensive error handling:

- **Database Errors**: Connection issues, schema problems
- **API Errors**: Network issues, rate limits, invalid responses
- **Processing Errors**: NLP failures, analysis errors
- **File System Errors**: Permission issues, disk space

All errors are logged with detailed information for debugging.

## Independence Verification

To verify the script is completely independent, run the test:

```bash
python test_rune_once_independence.py
```

This will confirm:
- ✅ All imports work without scheduler
- ✅ Functions are available independently
- ✅ No scheduler dependencies exist

## Scheduling

Since `rune_once.py` is completely independent, you can schedule it with any external scheduler:

### Linux/macOS (cron)
```bash
# Run daily at 2:30 AM
30 2 * * * cd /path/to/Stockometry && python src/rune_once.py
```

### Windows Task Scheduler
- Create a new task
- Set trigger to run daily at 2:30 AM
- Action: Start a program
- Program: `python`
- Arguments: `src/rune_once.py`
- Start in: `C:\path\to\Stockometry`

### Docker/Container
```dockerfile
# Add to your Dockerfile
COPY src/rune_once.py /app/
CMD ["python", "/app/rune_once.py"]
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're running from the project root
   - Check that all dependencies are installed

2. **Database Connection Issues**
   - Verify `.env` file has correct database credentials
   - Ensure database server is running

3. **API Key Issues**
   - Check `NEWS_API_KEY` in `.env` file
   - Verify API key is valid and has sufficient quota

4. **Permission Issues**
   - Ensure write permissions for `output/` directory
   - Check log file write permissions

### Debug Mode

For detailed debugging, check the log file:
```bash
tail -f rune_once.log
```

## Performance

Typical execution times:
- **News Collection**: 5-15 seconds
- **Market Data**: 10-30 seconds  
- **NLP Processing**: 20-60 seconds (depends on article count)
- **Analysis**: 5-15 seconds
- **Total**: 40-120 seconds

## Security Notes

- **API Keys**: Never commit API keys to version control
- **Database**: Uses production database - ensure proper access controls
- **Logs**: Logs may contain sensitive information - secure appropriately

## Support

If you encounter issues:
1. Check the log file (`rune_once.log`)
2. Verify configuration files (`.env`, `settings.yml`)
3. Ensure all dependencies are installed
4. Check database and API connectivity

---

**Note**: This script is designed to be completely independent and can be run anywhere without the full Stockometry scheduler infrastructure.
