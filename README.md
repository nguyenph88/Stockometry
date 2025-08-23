# Stockometry - Version 2.0.0

## Overview
Stockometry is a **two-stage financial analysis system** that combines historical trend analysis with real-time news impact assessment to generate actionable trading signals. The system analyzes 11 market sectors and provides buy/sell recommendations based on sentiment trends and current events.

## Two-Stage Analysis Logic
1. **Historical Trend Analysis** (Last 6 days): Identifies sectors with consistent positive/negative sentiment trends
2. **Today's Impact Analysis**: Evaluates today's high-impact news events and their sector implications

The final, high-confidence prediction comes when these two things align. For example, if the Technology sector has a positive historical trend and there's a positive impact event today, the bot flags it as a strong signal and then drills down to find the specific stocks mentioned in today's news.

## ☕ Support the Project

If you find Stockometry helpful, consider supporting the development:

[![GitHub Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-Support%20nguyenph88-red?style=for-the-badge&logo=github)](https://github.com/sponsors/nguyenph88)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Support%20nguyenph88-FFDD00?style=for-the-badge&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/nguyenph88)

Your support helps maintain and improve Stockometry! 🚀

## Key Features
- **11-Sector Coverage**: Technology, Healthcare, Financial Services, Consumer Discretionary, Consumer Staples, Energy, Industrials, Materials, Real Estate, Communication Services, Utilities
- **NLP-Powered Analysis**: Uses spaCy for entity extraction and FinBERT for financial sentiment analysis
- **Database-First Storage**: PostgreSQL as primary storage with on-demand JSON export
- **Modular Architecture**: Plug-and-play package structure for FastAPI integration
- **Standalone Operation**: Can run independently or as part of larger systems
- **Scheduled Analysis**: Automated daily analysis with configurable timing

## Quick Start

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd Stockometry

# Install dependencies
pip install -r requirements.txt

# Install spaCy model
python -m spacy download en_core_web_sm

# Set up configuration
cp stockometry/config/settings.yml.template stockometry/config/settings.yml
# Edit settings.yml with your database and API credentials
```

### Database Setup
```bash
# Initialize database
python -c "from stockometry.database import init_db; init_db()"
```

### Run Analysis
```bash
# Run once (standalone)
python -m stockometry.cli.run_once

# Start scheduler
python -m stockometry.scheduler.scheduler

# Export reports
python -m stockometry.utils.export_reports latest
```

## Usage Examples

### Standalone Analysis
```python
from stockometry.cli.run_once import run_analysis_and_save

# Run complete analysis pipeline
success = run_analysis_and_save()
```

### FastAPI Integration
```python
from fastapi import FastAPI
from stockometry.api.routes import router

app = FastAPI()
app.include_router(router, prefix="/api/v1")
```

### Testing
Run the E2E tests with mock and fake data:
```python
python -m stockometry.tests.run_all_e2e_tests
```

Run the E2E tests with real workflow to test each components:
```python
python -m stockometry.tests.run_comprehensive_test
```

## Configuration

### Settings File
```yaml
# stockometry/config/settings.yml
environment: production
database:
  host: localhost
  port: 5432
  name: stockometry
  user: your_username
  password: your_password

news_api_key: your_news_api_key

scheduler:
  timezone: UTC
  news_interval_hours: 1
  final_report_hour: 2
  final_report_minute: 30
```

## Testing

### Run All Tests
```bash
python -m stockometry.tests.run_all_e2e_tests
```

## Documentation
- **[FAQs.md](stockometry/docs/FAQs.md)**: Frequently asked questions
- **[API_ENDPOINTS.md](stockometry/docs/API_ENDPOINTS.md)**: Complete API reference
- **[FASTAPI_INTEGRATION.md](stockometry/docs/FASTAPI_INTEGRATION.md)**: Integration guide

## Architecture

### Core Components
- **Collectors**: News and market data collection
- **NLP Processor**: Article analysis and feature extraction
- **Analyzers**: Historical trends and today's impact analysis
- **Synthesizer**: Combines analyses into final signals
- **Output Processor**: Database storage and JSON export

### Data Flow
1. **Collection**: News articles and market data
2. **Processing**: NLP analysis and feature extraction
3. **Analysis**: Historical trends and current impact
4. **Synthesis**: Signal generation and report creation
5. **Storage**: Database persistence and optional export

## 11-Sector Coverage
The system analyzes these market sectors:
- **Technology**: AAPL, MSFT, GOOGL, NVDA, TSLA, META, AMZN, CRM, ADBE, ORCL
- **Healthcare**: JNJ, PFE, UNH, ABBV, TMO, DHR, ABT, CVS, CI, BMY
- **Financial Services**: JPM, BAC, WFC, GS, MS, C, AXP, BLK, SPGI, CB
- **Consumer Discretionary**: AMZN, TSLA, HD, MCD, SBUX, NKE, TJX, LOW, BKNG, MAR
- **Consumer Staples**: PG, KO, PEP, WMT, COST, PM, MO, KMB, CL, GIS
- **Energy**: XOM, CVX, COP, EOG, SLB, OXY, VLO, MPC, PSX, DVN
- **Industrials**: BA, CAT, UNP, UPS, RTX, LMT, DE, GE, HON, ETN
- **Materials**: LIN, APD, FCX, NEM, DOW, DD, BLL, NUE, VMC, ALB
- **Real Estate**: PLD, AMT, EQIX, CCI, PSA, SPG, O, VICI, WELL, EQR
- **Communication Services**: GOOGL, META, NFLX, DIS, CMCSA, T, VZ, CHTR, TMUS, FOX
- **Utilities**: NEE, DUK, SO, D, AEP, XEL, SRE, WEC, ETR, AEE

## Signal Interpretation Guide

### Strong Buy/Sell Signals
- **Action**: Immediate attention required
- **Confidence**: High (0.8-1.0)
- **Risk**: Medium-High
- **Timing**: Act within 24-48 hours

### Buy/Sell Signals
- **Action**: Consider position changes
- **Confidence**: Medium (0.6-0.8)
- **Risk**: Medium
- **Timing**: Act within 1-3 days

### Weak Buy/Sell Signals
- **Action**: Monitor closely
- **Confidence**: Low-Medium (0.4-0.6)
- **Risk**: Low-Medium
- **Timing**: Wait for confirmation

### Hold/Wait Signals
- **Action**: Maintain current positions
- **Confidence**: Low (0.0-0.4)
- **Risk**: Low
- **Timing**: Re-evaluate in 24-48 hours

## Data Freshness
- **News Data**: Updated hourly
- **Market Data**: Updated daily at 1:00 AM UTC
- **NLP Processing**: Every 15 minutes
- **Full Analysis**: Daily at 2:30 AM UTC
- **Manual Runs**: On-demand via CLI or API

## Signal Types & Criteria

### Bullish Signals
- **Strong Buy**: Historical trend score > 0.6 AND today's impact score > 0.7
- **Buy**: Historical trend score > 0.4 AND today's impact score > 0.5
- **Weak Buy**: Historical trend score > 0.2 AND today's impact score > 0.3

### Bearish Signals
- **Strong Sell**: Historical trend score < -0.6 AND today's impact score < -0.7
- **Sell**: Historical trend score < -0.4 AND today's impact score < -0.5
- **Weak Sell**: Historical trend score < -0.2 AND today's impact score < -0.3

### Neutral Signals
- **Hold**: Scores between -0.2 and 0.2, or mixed signals
- **Wait**: Insufficient data or conflicting signals


## Notes
- All timestamps are in UTC
- Scores range from -1.0 (extremely bearish) to +1.0 (extremely bullish)
- Confidence levels: LOW (< 0.5), MEDIUM (0.5-0.7), HIGH (> 0.7)
- Risk levels: LOW, MEDIUM, HIGH based on signal strength and market volatility

## Dependencies
- **Database**: PostgreSQL, psycopg2
- **NLP**: spaCy, transformers, torch
- **Data**: yfinance, requests, pandas, numpy
- **Scheduling**: APScheduler
- **API**: FastAPI (optional)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for analytical and educational purposes only. It is **not financial advice**. The signals generated by this bot are based on algorithmic analysis and do not guarantee any specific outcome. Always conduct your own research and consult with a qualified financial advisor before making any investment decisions.