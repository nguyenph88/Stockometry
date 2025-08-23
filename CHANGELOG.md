# Changelog

All notable changes to Stockometry will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-22

### 🚀 Major Features
- **Database-First Architecture**: Complete redesign to use PostgreSQL as the single source of truth
- **Comprehensive E2E Testing**: New end-to-end test suite that validates the entire workflow
- **FastAPI Integration**: Full REST API with comprehensive endpoints for all functionality
- **Modular Package Structure**: Reorganized codebase for plug-and-play integration

### 🗄️ Database & Storage
- **Schema Redesign**: Enhanced database schema to store all report data including NLP features
- **New Columns Added**:
  - `articles` table: `nlp_features` (JSONB), `stock_symbol`, `sector`, `sentiment_score`, `impact_level`
  - `report_signals` table: `stock_symbol`
  - `daily_reports` table: `run_source`, `executive_summary`
- **Automatic Schema Migration**: Database initialization now automatically adds missing columns
- **Environment-Based Database Selection**: Automatic staging vs production database selection

### 🔌 API Endpoints
- **Health Check**: `GET /stockometry/health`
- **Configuration**: `GET /stockometry/config`
- **Reports**:
  - `GET /stockometry/reports` - List all reports
  - `GET /stockometry/reports/{id}` - Get specific report
  - `GET /stockometry/reports/latest` - Get latest report (full report)
- **Analysis**: `POST /stockometry/analyze` - Trigger analysis (async)
- **Signals**: `GET /stockometry/signals` - Get all signals
- **Export**: `GET /stockometry/export/{id}/json` - Export report to JSON
- **Scheduler Control**:
  - `POST /stockometry/scheduler/start` - Start scheduler
  - `POST /stockometry/scheduler/stop` - Stop scheduler
  - `GET /stockometry/scheduler/status` - Get scheduler status

### 🧪 Testing & Quality Assurance
- **Comprehensive E2E Test Suite**: 11-step workflow validation
  - Step 0: Drop all existing tables
  - Step 1: Database connection & schema initialization
  - Step 2: News collection & storage
  - Step 3: Market data collection & storage
  - Step 4: NLP processing & storage
  - Step 5: Analysis generation
  - Step 6: Report saving & database storage
  - Step 7: JSON export functionality
  - Step 8: API endpoints testing
  - Step 9: Test data cleanup
  - Step 10: Complete staging database cleanup
- **Database State Validation**: Verifies data integrity at each workflow step
- **Automatic Cleanup**: Three-level cleanup system ensuring pristine test environment
- **Real API Testing**: Tests actual NewsAPI and yfinance integrations

### 🔧 Core Improvements
- **NLP Processing**: Enhanced spaCy + FinBERT integration with robust error handling
- **Market Data Collection**: Fixed yfinance FutureWarning with explicit `auto_adjust=True`
- **Timezone Handling**: Fixed UTC vs local time issues in analysis modules
- **Error Handling**: Comprehensive error handling and fallback mechanisms

### 📁 File Structure Changes
- **New Test Files**:
  - `stockometry/tests/test_comprehensive_e2e.py` - Main E2E test suite
  - `stockometry/tests/run_comprehensive_test.py` - Test runner script
  - `stockometry/tests/README_COMPREHENSIVE_TEST.md` - Test documentation
- **Updated Core Files**:
  - `stockometry/database/connection.py` - Enhanced schema and migration
  - `stockometry/api/routes.py` - Complete API endpoint implementation
  - `stockometry/core/output/processor.py` - Database-first output processing
  - `stockometry/core/analysis/*.py` - Fixed timezone handling

### 🗑️ Removed Features
- **Automatic JSON File Creation**: No longer creates JSON files by default
- **Legacy Test Files**: Removed outdated milestone-based test files
- **Redundant Output**: Eliminated duplicate data storage between database and files

### 📚 Documentation
- **Comprehensive README**: Updated with new architecture and usage instructions
- **API Documentation**: Complete endpoint documentation with examples
- **Test Documentation**: Detailed testing guide with troubleshooting

---

## [1.0.0] - 2025-01-21

### 🚀 Initial Release
- **Basic Stockometry Functionality**: News collection, market data analysis, NLP processing
- **Simple Output**: Basic JSON file generation and database storage
- **Core Analysis**: Historical trend analysis and signal generation
- **Basic Testing**: Simple unit tests for core components

---

## Version History

- **v2.0.0** (Current): Complete architecture redesign, database-first approach, comprehensive testing
- **v1.0.0**: Initial release with basic functionality

---

## Migration Guide

### From v1.0.0 to v2.0.0

#### Breaking Changes
- **Output Format**: JSON files are no longer created automatically
- **Database Schema**: New columns have been added to existing tables
- **API Structure**: New REST API endpoints replace direct function calls

#### Migration Steps
1. **Update Database**: Run the application once to automatically migrate schema
2. **Update Code**: Replace direct function calls with API endpoints
3. **Update Tests**: Use new comprehensive E2E test suite
4. **Review Configuration**: Update `settings.yml` for new environment-based database selection

#### New Features to Adopt
- **API Integration**: Use REST endpoints for all operations
- **Database-First**: All data is now stored in PostgreSQL
- **On-Demand Export**: Use `/export/{id}/json` endpoint for JSON generation
- **Comprehensive Testing**: Run the new E2E test suite for validation

---

## Contributing

When adding new features or making changes:
1. Update this changelog with clear descriptions
2. Follow semantic versioning principles
3. Include breaking changes in major version updates
4. Document new API endpoints and database changes
5. Update tests to maintain comprehensive coverage

---

## Support

For issues or questions:
1. Check the comprehensive E2E test results
2. Review the API documentation
3. Check database schema and migration logs
4. Run individual test components for debugging
