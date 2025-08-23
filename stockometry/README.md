# Stockometry - Modular Package

**Version 2.0.0** - Database-first architecture with comprehensive E2E testing

## Overview
Stockometry is a **two-stage financial analysis system** that combines historical trend analysis with real-time news impact assessment to generate actionable trading signals. The system analyzes 11 market sectors and provides buy/sell recommendations based on sentiment trends and current events.

## ☕ Support the Project

If you find Stockometry helpful, consider supporting the development:

[![GitHub Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-Support%20nguyenph88-red?style=for-the-badge&logo=github)](https://github.com/sponsors/nguyenph88)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Support%20nguyenph88-FFDD00?style=for-the-badge&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/nguyenph88)

## Quick Start

### Installation
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Run Analysis
```bash
# Standalone mode
python -m stockometry.cli.run_once

# Start scheduler
python -m stockometry.scheduler.scheduler

# Run comprehensive E2E test
python -m stockometry.tests.run_comprehensive_test
```

### FastAPI Integration
```python
from fastapi import FastAPI
from stockometry.api.routes import router

app = FastAPI()
app.include_router(router)
```

## Key Features
- **11-Sector Coverage**: Technology, Healthcare, Financial Services, etc.
- **NLP-Powered Analysis**: spaCy + FinBERT for sentiment analysis
- **Database-First Storage**: PostgreSQL with on-demand JSON export
- **Comprehensive Testing**: 11-step E2E workflow validation
- **Modular Architecture**: Plug-and-play for any FastAPI app

## Documentation
- **[API_ENDPOINTS.md](docs/API_ENDPOINTS.md)**: Complete API reference
- **[CHANGELOG.md](../CHANGELOG.md)**: Version history and changes
- **[README.md](../README.md)**: Main project documentation

## License
MIT License - see [LICENSE](../LICENSE) for details.
