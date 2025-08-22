# Stockometry Modular Package

This is the modular version of Stockometry, organized for both standalone use and FastAPI integration.

## Structure

```
stockometry/
├── __init__.py                 # Main package entry point
├── core/                       # Core business logic
│   ├── collectors/            # Data collection (news, market data)
│   ├── nlp/                   # NLP processing
│   ├── analysis/              # Analysis logic
│   └── output/                # Output processing
├── cli/                       # Standalone CLI interface
│   ├── run_once.py            # One-time execution
│   └── scheduler.py           # Standalone scheduler
├── api/                       # FastAPI integration layer
│   └── routes.py              # API endpoints
├── config/                    # Configuration management
│   └── settings.py            # Unified settings
├── database/                  # Database layer
│   └── connection.py          # DB connection management
├── tests/                     # Test suite
│   ├── test_e2e.py           # Main E2E test
│   ├── test_e2e_*.py         # Scenario-specific E2E tests
│   ├── test_collectors.py    # Data collection tests
│   ├── test_database.py      # Database tests
│   └── run_all_e2e_tests.py  # Test runner
└── utils/                     # Shared utilities
```

## Usage

### Standalone Mode (Original Functionality)

```bash
# Run once (equivalent to original run_once.py)
python stockometry/cli/run_once.py

# Start scheduler (equivalent to original scheduler.py)
python stockometry/cli/scheduler.py
```

### FastAPI Integration

```python
from fastapi import FastAPI
from stockometry.api import create_router

app = FastAPI()
stockometry_router = create_router()
app.include_router(stockometry_router)

# Available endpoints:
# POST /stockometry/analyze          # Trigger manual analysis
# GET  /stockometry/reports/latest   # Get latest report
# GET  /stockometry/reports/{date}   # Get report by date
# GET  /stockometry/reports          # List recent reports
# GET  /stockometry/status           # Service status
```

### Direct Core Usage

```python
from stockometry.core import run_stockometry_analysis

# Run analysis with custom run source
success = run_stockometry_analysis(run_source="CUSTOM")
```

### Testing

```bash
# Run individual E2E test
python -m stockometry.tests.test_e2e

# Run all E2E tests
python -m stockometry.tests.run_all_e2e_tests

# Run specific scenario test
python -m stockometry.tests.test_e2e_bullish_tech
python -m stockometry.tests.test_e2e_bearish_financial
python -m stockometry.tests.test_e2e_mixed_signals
python -m stockometry.tests.test_e2e_edge_cases
```

## Migration Notes

- All original functionality is preserved
- Import paths have been updated to use relative imports
- Configuration and database connections remain the same
- All tests have been moved to the modular structure and updated

## Version

This is Stockometry v3.0.0 - Modular Edition
