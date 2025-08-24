# Changelog

All notable changes to Stockometry will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2025-01-23

### 🚀 Major Features
- **Docker Scheduler Service**: New independent scheduler service designed specifically for Docker containers
- **Service Separation**: Complete separation of scheduling logic from main FastAPI application
- **Container-Optimized Architecture**: Dedicated service running on port 8005 with minimal resource usage

### 🐳 Docker & Containerization
- **New Package**: `stockometry.scheduler_docker` - Independent scheduler package
- **Container Service**: `SchedulerDocker` class with Docker-specific optimizations
- **Port Configuration**: Dedicated service running on port 8005 (separate from main app on 8000)
- **Docker Compose**: Complete orchestration setup for multi-service deployment
- **Health Checks**: Built-in health monitoring and container lifecycle management

### 🔧 Architecture Improvements
- **Service Decoupling**: Main FastAPI app no longer handles scheduling operations
- **Clean API**: Removed all scheduler endpoints from main application routes
- **Single-Threaded Design**: Simplified scheduler using single thread instead of thread pool
- **Environment Awareness**: Automatic database selection based on `settings.yml` environment
- **Modern FastAPI**: Updated to use lifespan event handlers (replacing deprecated on_event)

### 📊 Scheduling Logic
- **News Collection**: Hourly news fetching (every hour)
- **Market Data**: Daily collection at 1:00 AM UTC
- **NLP Processing**: Hourly processing at 5 minutes past each hour (aligned with news collection)
- **Report Generation**: Daily synthesis at 2:30 AM UTC
- **Heartbeat**: 5-minute intervals to maintain container health

### 🗄️ Database & Configuration
- **Environment Respect**: Automatically uses staging vs production database based on settings
- **Database Initialization**: Automatic table creation with environment-aware database selection
- **Run Source Tracking**: All scheduled reports marked with "SCHEDULER_DOCKER" source
- **Connection Management**: Optimized for containerized database connections

### 🔌 API Endpoints (Docker Scheduler Service)
- **Service Control**: `/start`, `/stop`, `/restart` - Scheduler lifecycle management
- **Status Monitoring**: `/status`, `/health` - Service health and job status
- **Job Information**: `/jobs` - Detailed scheduled job information
- **Root Info**: `/` - Service information and available endpoints

### 🧹 Code Cleanup
- **Removed Scheduler Routes**: Cleaned up main API routes to focus on business logic
- **Package Cleanup**: Removed scheduler imports from main package `__init__.py`
- **Logging Simplification**: Removed file logging from `run_once.py` (console only)
- **Deprecation Fixes**: Updated FastAPI event handlers to modern lifespan approach

### 📁 New File Structure
- **New Package**: `stockometry/scheduler_docker/`
  - `__init__.py` - Package initialization
  - `scheduler_docker.py` - Core scheduler logic
  - `main.py` - FastAPI application with lifespan events
  - `requirements.txt` - Service dependencies
  - `Dockerfile` - Container build instructions
  - `docker-compose.yml` - Multi-service orchestration
  - `README.md` - Service documentation
  - `test_scheduler.py` - Standalone testing script

### 🗑️ Removed Features
- **Main App Scheduler**: All scheduler control endpoints removed from main API
- **Thread Pool**: Replaced 4-worker thread pool with single-threaded execution
- **File Logging**: Removed `.log` file generation from CLI tools
- **Deprecated FastAPI**: Replaced deprecated `on_event` with modern lifespan handlers

### 📚 Documentation Updates
- **Docker Scheduler README**: Comprehensive service documentation
- **API Cleanup**: Updated main API documentation to reflect removed scheduler endpoints
- **Service Architecture**: Clear separation between main app and scheduler service

---

## [2.1.0] - 2025-08-22

### 🐛 Bug Fixes & Improvements
- **Database Connection Issues**: Fixed "relation does not exist" errors during first run
- **Timezone Handling**: Resolved UTC vs local time inconsistencies in analysis modules
- **Fallback Logic**: Added fallback mechanism to use yesterday's articles if today's are unavailable
- **Database Initialization**: Added `/init_db` endpoint for manual database table creation
- **API Endpoint Fixes**: Fixed missing `confidence` column errors and `report_object` argument issues
- **NLP Pipeline**: Fixed `sentiment_pipeline` attribute errors with robust fallback handling

### 🔧 Core Improvements
- **Database Schema Migration**: Enhanced automatic column addition with `ALTER TABLE ADD COLUMN IF NOT EXISTS`
- **Connection Management**: Improved database connection handling with proper context management
- **Error Recovery**: Better error handling and recovery mechanisms throughout the pipeline
- **Test Infrastructure**: Enhanced test setup and cleanup procedures

### 📚 Documentation Updates
- **README Consolidation**: Merged content from `EXAMPLE.md` into main README for better accessibility
- **API Documentation**: Updated endpoint documentation to reflect current implementation
- **Donation Links**: Added GitHub Sponsors and Buy Me a Coffee links for project support

### 🧪 Testing Improvements
- **Comprehensive E2E Tests**: Enhanced test suite with better database isolation
- **Staging Database**: Improved staging database usage for comprehensive testing
- **Test Cleanup**: Better cleanup procedures to ensure pristine test environment

---

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

- **v2.1.0** (Current): Bug fixes, timezone handling improvements, fallback logic, enhanced testing
- **v2.0.0**: Complete architecture redesign, database-first approach, comprehensive testing
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
