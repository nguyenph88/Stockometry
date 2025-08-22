# Stockometry - Version 3.0

## Overview
Stockometry is a **two-stage financial analysis system** that combines historical trend analysis with real-time news impact assessment to generate actionable trading signals. The system analyzes 11 market sectors and provides buy/sell recommendations based on sentiment trends and current events.

## Two-Stage Analysis Logic
1. **Historical Trend Analysis** (Last 6 days): Identifies sectors with consistent positive/negative sentiment trends
2. **Today's Impact Analysis**: Evaluates today's high-impact news events and their sector implications

## Key Features
- **11-Sector Coverage**: Technology, Healthcare, Financial Services, Consumer Discretionary, Consumer Staples, Energy, Industrials, Materials, Real Estate, Communication Services, Utilities
- **NLP-Powered Analysis**: Uses spaCy for entity extraction and FinBERT for financial sentiment analysis
- **Database-First Storage**: PostgreSQL as primary storage with on-demand JSON export
- **Modular Architecture**: Plug-and-play package structure for FastAPI integration
- **Standalone Operation**: Can run independently or as part of larger systems
- **Scheduled Analysis**: Automated daily analysis with configurable timing
- **Comprehensive Testing**: Full E2E test suite with shared test utilities

## Modular Structure
```
stockometry/
├── core/           # Core business logic and analysis
├── cli/            # Command-line interfaces
├── api/            # FastAPI integration
├── config/         # Configuration management
├── database/       # Database connection and management
├── scheduler/      # Scheduled analysis functionality
├── utils/          # Utility functions and tools
├── tests/          # Test suite and utilities
└── docs/           # Documentation files
```

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

# Set up environment variables
cp stockometry/config/.env.example stockometry/config/.env
# Edit .env with your database and API credentials
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

### Scheduled Operation
```python
from stockometry.scheduler.scheduler import main

# Start scheduled analysis
main()
```

### Export Reports
```python
from stockometry.utils.export_reports import export_latest_report

# Export latest analysis to JSON
export_latest_report()
```

### FastAPI Integration
```python
from fastapi import FastAPI
from stockometry.api.routes import router

app = FastAPI()
app.include_router(router, prefix="/api/v1")
```

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
# stockometry/config/settings.yml
database:
  host: localhost
  port: 5432
  name: stockometry
  user: your_username
  password: your_password

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

### Individual Test Scenarios
```bash
# Bullish Technology signals
python -m stockometry.tests.test_e2e_bullish_tech

# Bearish Financial signals
python -m stockometry.tests.test_e2e_bearish_financial

# Mixed market signals
python -m stockometry.tests.test_e2e_mixed_signals

# Edge cases and error handling
python -m stockometry.tests.test_e2e_edge_cases
```

## Documentation
- **[EXAMPLE.md](stockometry/docs/EXAMPLE.md)**: JSON output structure and signal interpretation
- **[README_RUNE_ONCE.md](stockometry/docs/README_RUNE_ONCE.md)**: Standalone execution guide
- **[FAQs.md](stockometry/docs/FAQs.md)**: Frequently asked questions
- **[WHAT_THIS_TOOL_DOES.md](stockometry/docs/WHAT_THIS_TOOL_DOES.md)**: Core functionality explanation

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

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support
- **Issues**: Report bugs and request features
- **Documentation**: Comprehensive guides and examples
- **Testing**: Full test suite for validation
- **Examples**: Working code samples and use cases