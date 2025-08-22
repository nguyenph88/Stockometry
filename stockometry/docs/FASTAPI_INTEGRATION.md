# FastAPI Integration Guide

This guide explains how to integrate Stockometry into your FastAPI application as a plug-and-play module.

## Quick Start

### 1. Install Stockometry

```bash
# Option 1: Install as a package (recommended)
pip install stockometry

# Option 2: Copy the stockometry folder to your project
cp -r stockometry/ /path/to/your/fastapi/project/
```

### 2. Basic Integration

```python
from fastapi import FastAPI
from stockometry.api import router as stockometry_router

app = FastAPI(title="My Financial App")
app.include_router(stockometry_router)
```

### 3. Run Your App

```bash
uvicorn main:app --reload
```

## Available Endpoints

### Analysis & Reports

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stockometry/analyze` | POST | Trigger manual analysis |
| `/stockometry/reports/latest` | GET | Get latest report |
| `/stockometry/reports/{report_date}` | GET | Get report by date |
| `/stockometry/reports` | GET | List recent reports |
| `/stockometry/reports/{report_id}/full` | GET | Get complete report with signals |
| `/stockometry/signals/{report_id}` | GET | Get trading signals for a report |

### Export & Data

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stockometry/export/{report_id}/json` | GET | Export report as JSON |
| `/stockometry/analyze/today` | GET | Get today's analysis |
| `/stockometry/analyze/historical` | GET | Get historical trends |

### Configuration & Control

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stockometry/config` | GET | View configuration |
| `/stockometry/scheduler/start` | POST | Start scheduler |
| `/stockometry/scheduler/stop` | POST | Stop scheduler |
| `/stockometry/scheduler/status` | GET | Get scheduler status |
| `/stockometry/status` | GET | Service health check |

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stockometry
DB_USER=your_user
DB_PASSWORD=your_password

# News API
NEWS_API_KEY=your_news_api_key

# Environment
ENVIRONMENT=production
```

### Settings File

Create `stockometry/config/settings.yml`:

```yaml
environment: production
log_level: INFO

database:
  host: localhost
  port: 5432
  database: stockometry
  user: your_user
  password: your_password

news_api_key: your_news_api_key

market_data:
  tickers: ["AAPL", "GOOGL", "MSFT", "TSLA"]
  period: "1mo"

scheduler:
  timezone: "UTC"
  news_interval_hours: 1
  market_data_hour: 1
  nlp_interval_minutes: 15
  final_report_hour: 2
  final_report_minute: 30
```

## Advanced Integration

### Custom Middleware

```python
from fastapi import FastAPI, Request
from stockometry.api import router as stockometry_router
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.include_router(stockometry_router)
```

### Authentication Integration

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from stockometry.api import router as stockometry_router

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Implement your token verification logic
    if not credentials.credentials == "valid_token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

app = FastAPI()
app.include_router(stockometry_router, dependencies=[Depends(verify_token)])
```

### Database Connection Pooling

```python
from fastapi import FastAPI
from stockometry.database import init_db
from stockometry.api import router as stockometry_router

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Initialize database with custom connection pool
    init_db()
    print("Database initialized with connection pooling")

app.include_router(stockometry_router)
```

## Example Use Cases

### 1. Financial Dashboard

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from stockometry.api import router as stockometry_router

app = FastAPI()
app.include_router(stockometry_router)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return """
    <html>
        <head><title>Financial Dashboard</title></head>
        <body>
            <h1>Financial Dashboard</h1>
            <div id="stockometry-widget">
                <h2>Market Signals</h2>
                <div id="signals"></div>
            </div>
            <script>
                // Fetch latest signals from /stockometry/reports/latest
                fetch('/stockometry/reports/latest')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('signals').innerHTML = 
                            '<p>' + data.executive_summary + '</p>';
                    });
            </script>
        </body>
    </html>
    """
```

### 2. Trading Bot Integration

```python
from fastapi import FastAPI, BackgroundTasks
from stockometry.api import router as stockometry_router
from stockometry.core import run_stockometry_analysis

app = FastAPI()
app.include_router(stockometry_router)

@app.post("/trading/signals/check")
async def check_trading_signals(background_tasks: BackgroundTasks):
    """Check for new trading signals and execute trades"""
    
    # Run analysis in background
    background_tasks.add_task(run_stockometry_analysis, "ONDEMAND")
    
    return {
        "message": "Analysis started",
        "status": "checking_signals"
    }

@app.get("/trading/signals/active")
async def get_active_signals():
    """Get currently active trading signals"""
    # This would integrate with your trading system
    return {
        "active_signals": [],
        "last_updated": "2024-01-01T00:00:00Z"
    }
```

### 3. News Monitoring Service

```python
from fastapi import FastAPI, WebSocket
from stockometry.api import router as stockometry_router
from stockometry.core.analysis.today_analyzer import analyze_todays_impact

app = FastAPI()
app.include_router(stockometry_router)

@app.websocket("/ws/news")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Analyze today's news every 5 minutes
            import asyncio
            await asyncio.sleep(300)
            
            analysis = analyze_todays_impact()
            if analysis.get("signals"):
                await websocket.send_json({
                    "type": "new_signals",
                    "data": analysis
                })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

## Error Handling

### Custom Error Responses

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from stockometry.api import router as stockometry_router

app = FastAPI()
app.include_router(stockometry_router)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": "2024-01-01T00:00:00Z",
            "path": str(request.url)
        }
    )
```

## Testing

### Unit Tests

```python
import pytest
from fastapi.testclient import TestClient
from stockometry.api import router as stockometry_router
from fastapi import FastAPI

app = FastAPI()
app.include_router(stockometry_router)
client = TestClient(app)

def test_get_status():
    response = client.get("/stockometry/status")
    assert response.status_code == 200
    assert "status" in response.json()

def test_trigger_analysis():
    response = client.post("/stockometry/analyze")
    assert response.status_code == 200
    assert response.json()["run_source"] == "ONDEMAND"
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  stockometry-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=stockometry
      - DB_USER=stockometry
      - DB_PASSWORD=password
    depends_on:
      - postgres
    volumes:
      - ./stockometry/config:/app/stockometry/config

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=stockometry
      - POSTGRES_USER=stockometry
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check database credentials in settings
   - Ensure PostgreSQL is running
   - Verify network connectivity

2. **Import Errors**
   - Ensure Stockometry is properly installed
   - Check Python path and virtual environment
   - Verify all dependencies are installed

3. **Scheduler Issues**
   - Check if scheduler is already running
   - Verify timezone settings
   - Check database permissions

### Debug Mode

Enable debug logging in your settings:

```yaml
log_level: DEBUG
```

## Support

For issues and questions:
- Check the main README.md
- Review the test files for usage examples
- Check the configuration files for proper setup

## Version Compatibility

- **FastAPI**: >= 0.104.0
- **Python**: >= 3.8
- **Stockometry**: 3.0.0+
