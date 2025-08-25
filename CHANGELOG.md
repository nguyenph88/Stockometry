# Changelog

All notable changes to this project will be documented in this file.

## [2.4.0] - 2025-01-23

### Changed
- **Market-Aligned Daily Report Schedule**: Updated daily report timing to align with actual stock market hours
  - Morning Report: 06:00 UTC (US pre-market, European morning)
  - Midday Report: 14:00 UTC (US morning trading, European midday)
  - Evening Report: 22:00 UTC (US market close, complete daily coverage)
  - **Impact**: Better data quality, market-relevant timing, improved user experience
  - **Files**: `scheduler_docker.py`, `scheduler_standalone.py`, `backfill/config.py`

## [2.3.0] - 2025-01-23

### Added
- **Enhanced Daily Reporting**: Implemented 3-times daily report generation for fresher insights
  - Morning Report: 2:15 AM UTC (full daily analysis)
  - Midday Update: 10:15 AM UTC (quick refresh with new data)
  - Evening Summary: 6:15 PM UTC (end-of-day wrap-up)
  - **Benefits**: More frequent updates, better market responsiveness, improved data freshness
  - **Files**: `scheduler_docker.py`, `scheduler_standalone.py`

### Changed
- **Scheduler Optimization**: Removed heartbeat mechanisms from both schedulers for cleaner operation
  - **Docker Scheduler**: Removed HEALTHCHECK and /health endpoint
  - **Standalone Scheduler**: Removed heartbeat job
  - **Benefits**: Reduced log noise, simpler operation, better performance

## [2.2.0] - 2025-01-22

### Added
- **Backfill System**: New package for checking missing daily reports
  - **Features**: Missing report detection, configurable schedule, ONDEMAND exclusion
  - **CLI**: Simple menu-based interface with table output
  - **Database**: Environment-aware (staging/production) database selection
  - **Files**: `stockometry/backfill/` package with all components

### Changed
- **Database Connection**: Enhanced with automatic environment-based database selection
  - **Staging**: Uses `stockometry_staging` database
  - **Production**: Uses `stockometry` database
  - **Configuration**: Driven by `settings.yml` environment setting

## [2.1.0] - 2025-01-21

### Added
- **Enhanced Scheduler**: Added heartbeat monitoring to standalone scheduler
  - **Monitoring**: Health check every 30 seconds
  - **Logging**: Heartbeat status logging
  - **File**: `scheduler_standalone.py`

## [2.0.0] - 2025-01-20

### Added
- **Docker Support**: Added Docker containerization for scheduler service
  - **Dockerfile**: Multi-stage build with Python 3.11
  - **Docker Compose**: Service orchestration
  - **Health Check**: Container health monitoring
  - **Files**: `scheduler_docker/` directory

### Changed
- **Scheduler Architecture**: Refactored to support both standalone and Docker modes
  - **Standalone**: Direct Python execution
  - **Docker**: Containerized service with FastAPI
  - **Configuration**: Unified configuration management

## [1.0.0] - 2025-01-19

### Added
- **Initial Release**: Core Stockometry functionality
  - **Market Data Collection**: Automated stock data gathering
  - **News Analysis**: Financial news processing and sentiment analysis
  - **Report Generation**: Daily market analysis reports
  - **Scheduling**: Automated daily report generation
