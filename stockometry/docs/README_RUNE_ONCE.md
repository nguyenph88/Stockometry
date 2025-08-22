# Stockometry Run Once Guide

## Overview
The `run_once.py` script provides a standalone execution of the complete Stockometry analysis pipeline without requiring the scheduler.

## Features
- **Complete Pipeline Execution**: Runs the entire analysis from data collection to final report
- **Standalone Operation**: No dependency on scheduler or background processes
- **Immediate Results**: Generates and saves analysis results immediately
- **Database Storage**: Saves results to PostgreSQL database
- **On-Demand JSON Export**: Optional JSON file export for immediate use

## Usage

### Basic Execution
```bash
python -m stockometry.cli.run_once
```

### With Logging
```bash
python -m stockometry.cli.run_once > run_once.log 2>&1
```

### From Python
```python
from stockometry.cli.run_once import run_analysis_and_save

# Run the complete analysis
success = run_analysis_and_save()
if success:
    print("Analysis completed successfully")
else:
    print("Analysis failed")
```

## What It Does

### 1. Data Collection
- **News Collection**: Fetches latest financial news from NewsAPI
- **Market Data**: Retrieves current stock prices and market data from Yahoo Finance
- **NLP Processing**: Analyzes news articles for sentiment and entity extraction

### 2. Analysis Pipeline
- **Historical Analysis**: Analyzes 6-day trends for all market sectors
- **Today's Analysis**: Evaluates today's high-impact news events
- **Synthesis**: Combines historical and current analysis into final signals

### 3. Output Processing
- **Database Storage**: Saves complete analysis to PostgreSQL
- **Report Generation**: Creates structured report with signals and insights
- **Optional Export**: Can export to JSON format if needed

## Output

### Database Tables
- `daily_reports`: Main analysis reports
- `report_signals`: Individual sector signals
- `signal_sources`: Source articles for each signal
- `predicted_stocks`: Stock-specific predictions

### Report Structure
- **Executive Summary**: High-level market overview
- **Sector Signals**: Buy/Sell/Hold recommendations for each sector
- **Confidence Scores**: Signal strength and reliability metrics
- **Risk Assessment**: Market risk levels and considerations

## Configuration

### Environment Variables
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stockometry
DB_USER=your_username
DB_PASSWORD=your_password

# API Keys
NEWS_API_KEY=your_news_api_key
```

### Settings File
```yaml
# settings.yml
database:
  host: localhost
  port: 5432
  name: stockometry
  user: your_username
  password: your_password

apis:
  news_api_key: your_news_api_key
```

## Dependencies

### Required Packages
```
psycopg2-binary>=2.9.0
yfinance>=0.2.0
requests>=2.28.0
spacy>=3.5.0
transformers>=4.20.0
torch>=1.12.0
pandas>=1.5.0
numpy>=1.21.0
```

### NLP Models
```bash
# Install spaCy model
python -m spacy download en_core_web_sm

# FinBERT will be downloaded automatically on first use
```

## Error Handling

### Common Issues
1. **Database Connection**: Ensure PostgreSQL is running and credentials are correct
2. **API Limits**: NewsAPI has rate limits; check your plan
3. **NLP Models**: Ensure spaCy model is installed
4. **Memory**: Large news datasets may require sufficient RAM

### Logging
The script provides detailed logging:
- **Console Output**: Real-time progress and results
- **File Logging**: Detailed logs saved to `run_once.log`
- **Error Reporting**: Clear error messages and stack traces

## Performance

### Execution Time
- **Typical**: 2-5 minutes for complete analysis
- **Factors**: Number of news articles, database performance, API response times
- **Optimization**: Database indexing, parallel processing for large datasets

### Resource Usage
- **Memory**: 100-500 MB depending on news volume
- **CPU**: Moderate usage during NLP processing
- **Network**: API calls to NewsAPI and Yahoo Finance

## Integration

### With Scheduler
The `run_once.py` script can be integrated with the scheduler:
```python
from stockometry.scheduler.scheduler import run_synthesis_and_save

# Use the same analysis function
result = run_synthesis_and_save()
```

### With API
The analysis results are accessible via the FastAPI endpoints:
```python
from stockometry.api.routes import get_latest_report

# Get the latest analysis results
report = get_latest_report()
```

## Troubleshooting

### Database Issues
```bash
# Check database connection
python -c "from stockometry.database import get_db_connection; print('DB OK')"

# Initialize database
python -c "from stockometry.database import init_db; init_db()"
```

### API Issues
```bash
# Test NewsAPI
python -c "import requests; print(requests.get('https://newsapi.org/v2/top-headlines?country=us&apiKey=YOUR_KEY').status_code)"

# Test Yahoo Finance
python -c "import yfinance as yf; print(yf.Ticker('AAPL').info['regularMarketPrice'])"
```

### NLP Issues
```bash
# Test spaCy
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('spaCy OK')"

# Test FinBERT
python -c "from transformers import pipeline; classifier = pipeline('sentiment-analysis', model='ProsusAI/finbert'); print('FinBERT OK')"
```

## Best Practices

### Production Use
1. **Environment Isolation**: Use virtual environments
2. **Configuration Management**: Use environment variables for secrets
3. **Logging**: Implement proper log rotation
4. **Monitoring**: Track execution time and success rates
5. **Error Handling**: Implement retry logic for transient failures

### Development
1. **Testing**: Use the test suite before deployment
2. **Validation**: Verify database schema and data integrity
3. **Documentation**: Keep configuration and usage docs updated
4. **Version Control**: Track changes and maintain rollback capability

## Support

### Documentation
- **Main README**: Project overview and setup
- **EXAMPLE.md**: JSON output structure and examples
- **FAQs.md**: Common questions and solutions
- **WHAT_THIS_TOOL_DOES.md**: Core functionality explanation

### Testing
- **Unit Tests**: Individual component testing
- **E2E Tests**: Complete pipeline validation
- **Test Setup**: Shared test utilities and data

### Community
- **Issues**: Report bugs and request features
- **Discussions**: Share ideas and solutions
- **Contributions**: Submit improvements and fixes
