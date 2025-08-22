# Stockometry - Version 3.0

## Overview
Stockometry is a **two-stage financial analysis system** that combines historical trend analysis with real-time news impact assessment to generate actionable trading signals. The system analyzes 11 market sectors and provides buy/sell recommendations based on sentiment trends and current events.

## Two-Stage Analysis Logic
1. **Historical Trend Analysis** (Last 6 days): Identifies sectors with consistent positive/negative sentiment trends
2. **Today's Impact Analysis**: Evaluates today's high-impact news events and their sector implications

The final, high-confidence prediction comes when these two things align. For example, if the Technology sector has a positive historical trend and there's a positive impact event today, the bot flags it as a strong signal and then drills down to find the specific stocks mentioned in today's news.

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
- **[EXAMPLE.md](stockometry/docs/EXAMPLE.md)**: JSON output structure and signal interpretation
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

## Dependencies
- **Database**: PostgreSQL, psycopg2
- **NLP**: spaCy, transformers, torch
- **Data**: yfinance, requests, pandas, numpy
- **Scheduling**: APScheduler
- **API**: FastAPI (optional)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.