# Stockometry Scheduler Docker Service

This is a Docker-optimized scheduler service for Stockometry that runs independently from the main FastAPI application. It provides all the same scheduling functionality but is specifically designed for Docker container environments.

## Features

- **Zero Impact**: No modifications to existing Stockometry code
- **Docker Optimized**: Built specifically for containerized environments
- **Same Functionality**: All the same scheduled tasks as the main scheduler
- **Independent Service**: Runs on its own port (8005) with separate endpoints
- **Auto-start**: Automatically starts the scheduler when the container starts
- **Health Monitoring**: Built-in health checks for container orchestration

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│   Main FastAPI App  │    │  Scheduler Docker  │
│   (Port 8000)       │    │   (Port 8005)      │
│                     │    │                     │
│ - Business Logic    │    │ - Scheduler Control │
│ - API Endpoints     │    │ - Scheduled Jobs    │
│ - No Scheduler      │    │ - Health Monitoring │
└─────────────────────┘    └─────────────────────┘
         │                           │
         └───────────┬───────────────┘
                     │
              ┌─────────────┐
              │  Database   │
              │  (Shared)   │
              └─────────────┘
```

## Scheduled Jobs

The Scheduler Docker runs the same jobs as the main scheduler:

1. **News Collection** - Every hour
2. **Market Data Collection** - Daily at 1:00 AM UTC
3. **NLP Processing** - Every 15 minutes
4. **Final Report Generation** - Daily at 2:30 AM UTC
5. **Heartbeat** - Every 5 minutes (keeps scheduler alive in Docker)

## API Endpoints

### Base URL: `http://localhost:8005`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information and available endpoints |
| `/start` | POST | Start the scheduler |
| `/stop` | POST | Stop the scheduler |
| `/restart` | POST | Restart the scheduler |
| `/status` | GET | Get current scheduler status |
| `/health` | GET | Health check for container monitoring |
| `/jobs` | GET | Get detailed job information |

## Quick Start

### 1. Build and Run with Docker Compose

```bash
# From the Stockometry root directory
cd stockometry/scheduler_docker
docker-compose up --build
```

This will start both services:
- Main FastAPI app on port 8000
- Scheduler Docker on port 8005

### 2. Manual Docker Build

```bash
# Build the scheduler image
docker build -f stockometry/scheduler_docker/Dockerfile -t stockometry-scheduler-docker .

# Run the scheduler container
docker run -d \
  --name stockometry-scheduler-docker \
  -p 8005:8005 \
  -e DATABASE_URL=your_database_url \
  stockometry-scheduler-docker
```

### 3. Test the Scheduler

```bash
# Check service status
curl http://localhost:8005/

# Start the scheduler
curl -X POST http://localhost:8005/start

# Check scheduler status
curl http://localhost:8005/status

# Health check
curl http://localhost:8005/health
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | Required |
| `SCHEDULER_ENV` | Environment identifier | `scheduler_docker` |
| `PYTHONPATH` | Python path for imports | `/app` |

## Integration with Main App

The Scheduler Docker is completely independent but can be integrated with your main FastAPI application:

### Option 1: Separate Services (Recommended)
- Main app handles business logic
- Scheduler service handles all scheduling
- Both share the same database
- Communicate via HTTP if needed

### Option 2: Health Check Integration
```python
# In your main FastAPI app
import httpx

async def check_scheduler_health():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://scheduler:8005/health")
        return response.json()
```

## Monitoring and Logs

### View Scheduler Logs
```bash
docker logs stockometry-scheduler-docker
```

### Check Scheduler Status
```bash
curl http://localhost:8005/status | jq
```

### Monitor Jobs
```bash
curl http://localhost:8005/jobs | jq
```

## Troubleshooting

### Scheduler Won't Start
1. Check database connectivity
2. Verify environment variables
3. Check container logs: `docker logs stockometry-scheduler-docker`

### Jobs Not Running
1. Check scheduler status: `GET /status`
2. Verify database initialization
3. Check job configuration in logs

### Container Health Issues
1. Check health endpoint: `GET /health`
2. Verify port binding
3. Check resource constraints

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt
pip install -e ../../

# Run locally
python -m stockometry.scheduler_docker.main
```

### Testing
```bash
# Test scheduler endpoints
pytest tests/test_scheduler_docker.py

# Integration tests
pytest tests/test_integration.py
```

## Security Considerations

- The scheduler runs on a separate port (8005)
- CORS is configured for Docker container communication
- Non-root user in container
- Health checks for monitoring
- Graceful shutdown handling

## Performance

- Optimized for Docker environments
- Thread pool with 4 workers
- Graceful handling of missed jobs (5-minute grace time)
- Heartbeat to prevent container death
- Efficient database connection management

## Migration from Main Scheduler

**No migration needed!** The Scheduler Docker:
- Uses the same core functions
- Shares the same database
- Runs the same jobs
- Can coexist with the main scheduler

Simply deploy both services and the Scheduler Docker will handle all scheduling tasks independently.
