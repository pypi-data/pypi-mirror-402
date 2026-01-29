# Nexarch SDK - Python

Runtime architecture intelligence SDK for FastAPI applications.

## Installation

### From PyPI (once published)

```bash
pip install nexarch-sdk
```

### From Source (Development)

```bash
cd SDK
pip install -e .
```

## Quick Start

### Basic Usage

```python
from fastapi import FastAPI
from nexarch import NexarchSDK

# Create your FastAPI app
app = FastAPI(title="My API")

# Initialize Nexarch SDK
sdk = NexarchSDK(
    api_key="your_api_key_here",
    environment="production",
    log_file="nexarch_telemetry.json"
)

# Attach SDK to your app (auto-injects middleware and router)
sdk.init(app)

# Your existing routes
@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": "John Doe"}
```

### One-Line Initialization

```python
from fastapi import FastAPI
from nexarch import NexarchSDK

app = FastAPI()

# Initialize in one line
NexarchSDK.start(app, api_key="your_api_key")
```

## What Gets Captured

The SDK automatically captures:

- **All HTTP Requests**: Method, path, query parameters, latency, status codes
- **All Errors**: Exception types, messages, full tracebacks
- **Performance Metrics**: Request latency, throughput, error rates
- **Dependency Calls**: Database queries, external API calls (future)

## Auto-Injected Endpoints

The SDK automatically adds internal management endpoints:

```bash
# Check SDK health
GET /__nexarch/health

# Get all telemetry data
GET /__nexarch/telemetry

# Get telemetry statistics
GET /__nexarch/telemetry/stats

# Get only errors
GET /__nexarch/telemetry/errors

# Get only request spans
GET /__nexarch/telemetry/spans

# Clear all telemetry
DELETE /__nexarch/telemetry
```

## Local Telemetry Storage

All telemetry is stored locally in JSON format:

```json
[
  {
    "type": "span",
    "timestamp": "2026-01-16T10:30:00.000Z",
    "data": {
      "trace_id": "abc-123",
      "operation": "GET /users/1",
      "latency_ms": 45.2,
      "status_code": 200,
      "status": "ok"
    }
  },
  {
    "type": "error",
    "timestamp": "2026-01-16T10:31:00.000Z",
    "data": {
      "error_type": "ValueError",
      "error_message": "Invalid user ID",
      "traceback": "..."
    }
  }
]
```

## Configuration Options

```python
sdk = NexarchSDK(
    api_key="your_api_key",              # Required: Your Nexarch API key
    environment="production",             # Optional: Environment name
    log_file="nexarch_telemetry.json",   # Optional: Local log file path
    observation_duration="3h",            # Optional: How long to observe
    sampling_rate=1.0,                    # Optional: Sample rate (0.0-1.0)
    enable_local_logs=True                # Optional: Enable local logging
)
```

## Example: Complete FastAPI App

```python
from fastapi import FastAPI, HTTPException
from nexarch import NexarchSDK

app = FastAPI(title="User Service")

# Initialize Nexarch
sdk = NexarchSDK(
    api_key="demo_api_key",
    environment="production",
    log_file="telemetry.json"
)
sdk.init(app)

# Simulated database
users_db = {
    1: {"id": 1, "name": "Alice"},
    2: {"id": 2, "name": "Bob"}
}

@app.get("/")
def root():
    return {"message": "User Service API"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.post("/users")
def create_user(user: dict):
    user_id = max(users_db.keys()) + 1
    users_db[user_id] = {"id": user_id, **user}
    return users_db[user_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Building the Package

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# This creates:
# - dist/nexarch_sdk-0.1.0-py3-none-any.whl
# - dist/nexarch_sdk-0.1.0.tar.gz
```

## Publishing to PyPI

```bash
# Test PyPI (for testing)
twine upload --repository testpypi dist/*

# Production PyPI
twine upload dist/*
```

## Testing Locally

```bash
# Install in editable mode
pip install -e .

# Run your FastAPI app
python your_app.py

# Check telemetry
curl http://localhost:8000/__nexarch/telemetry/stats
```

## What Happens After Installation

1. **Middleware Injection**: SDK adds middleware to capture every request
2. **Router Auto-Injection**: Internal `/__nexarch/*` endpoints are added
3. **Local Logging**: Telemetry is written to JSON file in real-time
4. **No Code Changes**: Your existing routes work exactly as before

## Security & Privacy

- **No Source Code Access**: SDK only observes runtime behavior
- **No Payload Capture**: Request/response bodies are never logged
- **Header Sanitization**: Sensitive headers (auth, cookies) are redacted
- **Local First**: All data stored locally before optional remote sync

## Support

- Documentation: https://docs.nexarch.io
- GitHub: https://github.com/nexarch/nexarch-sdk
- Email: support@nexarch.io
