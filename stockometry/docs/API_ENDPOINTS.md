# Stockometry API Endpoints Reference

Complete reference for all available API endpoints in Stockometry 3.0.0.

## Base URL

All endpoints are prefixed with `/stockometry`

## Authentication

Currently, no authentication is required. For production use, implement appropriate authentication middleware.

## Response Models & Validation

All endpoints use Pydantic response models for consistent data structure and automatic validation. Input parameters are validated using FastAPI's built-in validation:

- **Path Parameters**: Validated with constraints (e.g., `report_id` must be ≥ 1)
- **Query Parameters**: Validated with ranges and descriptions (e.g., `limit` must be 1-100)
- **Date Format**: Must be YYYY-MM-DD format for date parameters
- **Response Models**: Ensure consistent API response structure

## Endpoints Overview

### 🔍 Analysis & Reports

#### Trigger Analysis
- **POST** `/stockometry/analyze`
- **Description**: Trigger a manual Stockometry analysis
- **Response**: Analysis status and run source
- **Example Response**:
```json
{
  "message": "Analysis started",
  "status": "running",
  "run_source": "ONDEMAND"
}
```

#### Get Latest Report
- **GET** `/stockometry/reports/latest`
- **Description**: Get the most recent Stockometry report with full details and signals
- **Response**: Complete report including all trading signals
- **Example Response**:
```json
{
  "report_id": 123,
  "report_date": "2024-01-15",
  "executive_summary": "Market shows bullish sentiment in technology sector...",
  "run_source": "SCHEDULED",
  "generated_at_utc": "2024-01-15T14:30:00Z",
  "signals": [
    {
      "signal_id": 456,
      "type": "TREND",
      "sector": "Technology",
      "direction": "UP",
      "confidence": 0.85,
      "details": "Strong positive sentiment in tech sector...",
      "source_articles": [
        {
          "title": "Tech Stocks Rally on AI Breakthrough",
          "url": "https://example.com/article1"
        }
      ]
    }
  ],
  "total_signals": 1
}
```

#### Get Report by Date
- **GET** `/stockometry/reports/by-date/{report_date}`
- **Parameters**: `report_date` (YYYY-MM-DD format, validated with regex)
- **Description**: Get report for a specific date
- **Response**: Basic report metadata for the specified date
- **Validation**: Date format must be YYYY-MM-DD

#### List Recent Reports
- **GET** `/stockometry/reports`
- **Query Parameters**: `limit` (default: 10, max: 100)
- **Description**: List recent reports with pagination
- **Response**: Array of reports with metadata

#### Get Full Report
- **GET** `/stockometry/reports/{report_id}/full`
- **Parameters**: `report_id` (integer)
- **Description**: Get complete report with all signals and analysis details
- **Response**: Full report including all trading signals
- **Example Response**:
```json
{
  "report_id": 123,
  "report_date": "2024-01-15",
  "executive_summary": "Market shows bullish sentiment...",
  "run_source": "SCHEDULED",
  "generated_at_utc": "2024-01-15T14:30:00Z",
  "signals": [
    {
      "signal_id": 456,
      "type": "TREND",
      "sector": "Technology",
      "direction": "UP",
      "confidence": 0.85,
      "details": "Strong positive sentiment in tech sector...",
      "source_articles": [
        {
          "title": "Tech Stocks Rally on AI Breakthrough",
          "url": "https://example.com/article1"
        }
      ]
    }
  ],
  "total_signals": 1
}
```

#### Get Report Signals
- **GET** `/stockometry/signals/{report_id}`
- **Parameters**: `report_id` (integer)
- **Description**: Get individual trading signals for a specific report
- **Response**: Array of signals with details

### 📊 Export & Data Analysis

#### Export Report as JSON
- **GET** `/stockometry/export/{report_id}/json`
- **Parameters**: `report_id` (integer)
- **Description**: Export a complete report in JSON format
- **Response**: Full report data in JSON format
- **Content-Type**: `application/json`

#### Today's Analysis
- **GET** `/stockometry/analyze/today`
- **Description**: Get today's high-impact news analysis (independent of full reports)
- **Response**: Today's analysis results
- **Example Response**:
```json
{
  "analysis_date": "2024-01-15",
  "signals": [
    {
      "type": "IMPACT",
      "sector": "Financial Services",
      "direction": "DOWN",
      "details": "Regulatory changes affecting banking sector...",
      "source_articles": [
        {
          "title": "New Banking Regulations Announced",
          "url": "https://example.com/article2"
        }
      ]
    }
  ],
  "summary_points": [
    "A high-impact event for the 'Financial Services' sector suggests a short-term move down."
  ],
  "total_signals": 1,
  "run_source": "ONDEMAND"
}
```

#### Historical Analysis
- **GET** `/stockometry/analyze/historical`
- **Query Parameters**: `days` (default: 6, range: 1-30)
- **Description**: Get historical trends analysis for the specified number of days
- **Response**: Historical analysis results with trends and signals

### ⚙️ Configuration & Control

#### Get Configuration
- **GET** `/stockometry/config`
- **Description**: View current Stockometry configuration (non-sensitive)
- **Response**: Configuration details
- **Example Response**:
```json
{
  "environment": "staging",
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "stockometry_staging",
    "active_database": "stockometry_staging"
  },
  "market_data": {
    "tickers_count": 15,
    "period": "1mo"
  },
  "scheduler": {
    "timezone": "UTC",
    "news_interval_hours": 1,
    "market_data_hour": 1,
    "nlp_interval_minutes": 15,
    "final_report_hour": 2
  },
  "analysis": {
    "historical_days": 6,
    "extreme_sentiment_threshold": 0.9
  }
}
```

#### Scheduler Control

##### Start Scheduler
- **POST** `/stockometry/scheduler/start`
- **Description**: Start the Stockometry scheduler
- **Response**: Scheduler status
- **Example Response**:
```json
{
  "status": "started",
  "message": "Scheduler started successfully"
}
```

##### Stop Scheduler
- **POST** `/stockometry/scheduler/stop`
- **Description**: Stop the Stockometry scheduler
- **Response**: Scheduler status
- **Example Response**:
```json
{
  "status": "stopped",
  "message": "Scheduler stopped successfully"
}
```

##### Get Scheduler Status
- **GET** `/stockometry/scheduler/status`
- **Description**: Get current scheduler status and job information
- **Response**: Detailed scheduler status
- **Example Response**:
```json
{
  "status": "running",
  "running": true,
  "jobs": [
    {
      "id": "news_fetcher",
      "next_run": "2024-01-15T15:00:00Z",
      "trigger": "interval[1:00:00]"
    },
    {
      "id": "market_data_fetcher",
      "next_run": "2024-01-16T01:00:00Z",
      "trigger": "cron[hour=1, minute=0]"
    }
  ],
  "total_jobs": 4
}
```

### 🏥 Health & Status

#### Service Status
- **GET** `/stockometry/status`
- **Description**: Get Stockometry service health status
- **Response**: Service health information
- **Example Response**:
```json
{
  "status": "healthy",
  "total_reports": 45,
  "latest_report": "2024-01-15T14:30:00Z",
  "version": "3.0.0"
}
```

## Error Responses

All endpoints return consistent error responses:

### HTTP 400 - Bad Request
```json
{
  "detail": "Invalid parameter value"
}
```

### HTTP 404 - Not Found
```json
{
  "detail": "Report 999 not found"
}
```

### HTTP 500 - Internal Server Error
```json
{
  "detail": "Failed to fetch report: Database connection error"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider implementing rate limiting middleware.

## Data Formats

### Date Format
All dates are returned in ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`

### Timezone
All timestamps are in UTC (Coordinated Universal Time)

### Signal Types
- `TREND`: Multi-day trend signals
- `IMPACT`: High-impact event signals
- `SENTIMENT`: Extreme sentiment signals

### Sector Values
- Technology
- Financial Services
- Healthcare
- Consumer Discretionary
- Consumer Staples
- Energy
- Industrials
- Materials
- Real Estate
- Utilities
- Communication Services

### Direction Values
- `UP`: Bullish signal
- `DOWN`: Bearish signal
- `NEUTRAL`: Neutral signal

## Usage Examples

### Python Requests
```python
import requests

# Trigger analysis
response = requests.post("http://localhost:8000/stockometry/analyze")
print(response.json())

# Get latest report
response = requests.get("http://localhost:8000/stockometry/reports/latest")
report = response.json()
print(f"Latest report: {report['executive_summary']}")

# Get today's analysis
response = requests.get("http://localhost:8000/stockometry/analyze/today")
analysis = response.json()
print(f"Found {analysis['total_signals']} signals today")
```

### JavaScript Fetch
```javascript
// Trigger analysis
fetch('/stockometry/analyze', { method: 'POST' })
  .then(response => response.json())
  .then(data => console.log('Analysis started:', data));

// Get latest report
fetch('/stockometry/reports/latest')
  .then(response => response.json())
  .then(report => console.log('Latest report:', report.executive_summary));
```

### cURL
```bash
# Trigger analysis
curl -X POST http://localhost:8000/stockometry/analyze

# Get latest report
curl http://localhost:8000/stockometry/reports/latest

# Get today's analysis
curl http://localhost:8000/stockometry/analyze/today
```

## Testing

### Test the API
1. Start your FastAPI application
2. Visit `http://localhost:8000/docs` for interactive API documentation
3. Use the Swagger UI to test endpoints
4. Check `http://localhost:8000/redoc` for alternative documentation

### Health Check
```bash
curl http://localhost:8000/stockometry/status
```

## Version History

- **3.0.0**: Initial API release with comprehensive endpoints
- Added full report access, signal details, and export functionality
- Added today's and historical analysis endpoints
- Added scheduler control endpoints
- Added configuration access endpoint

## Support

For API-related issues:
1. Check the service status endpoint
2. Review the error messages in responses
3. Check the application logs
4. Verify database connectivity
5. Ensure all required services are running
