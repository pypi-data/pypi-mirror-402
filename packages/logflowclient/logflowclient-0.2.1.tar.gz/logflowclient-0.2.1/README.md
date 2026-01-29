# LogFlow Python SDK

Simple, schema-less logging SDK for the LogFlow platform.

## Installation

```bash
pip install logflowclient
```

## Quick Start

```python
from logflow import Logger

# Initialize the logger with just your API key
logger = Logger(api_key="lf_your_api_key_here")

# Send a log - that's it!
logger.log(
    bucket="user_activity",
    data={
        "event": "profile_view",
        "user_id": "123",
        "profile_id": "456"
    }
)
```

No need to call `close()` - cleanup happens automatically!

## Features

- **Non-blocking**: Logs are queued and sent asynchronously in the background
- **Automatic batching**: Logs are batched to reduce HTTP overhead
- **Fail-safe**: Won't crash your application if logging fails
- **Retry logic**: Automatic retries with exponential backoff
- **Zero schema**: Send any JSON-serializable data structure

## Configuration

```python
logger = Logger(
    api_key="lf_your_api_key_here",        # Required: Your LogFlow API key (project auto-detected)
    api_url="https://...",                 # Optional: API URL (default: production URL)
    batch_size=10,                         # Optional: Logs to batch before sending (default: 10)
    flush_interval=5.0,                    # Optional: Seconds to wait before flushing (default: 5.0)
    max_retries=3,                         # Optional: Max retry attempts (default: 3)
    debug=False                            # Optional: Enable debug logging (default: False)
)
```

## Usage Examples

### Basic Logging

```python
from logflow import Logger

logger = Logger(api_key="lf_...")

# Log user activity
logger.log(
    bucket="user_activity",
    data={
        "event": "button_click",
        "button_id": "submit_form",
        "user_id": "user_123",
        "timestamp": "2026-01-18T10:30:00Z"
    }
)

# That's it! Logs are sent automatically in the background
# Cleanup happens automatically when your program exits
```

### Error Logging

```python
from logflow import Logger
import traceback

logger = Logger(api_key="lf_...", project_id="...")

try:
    # Your code
    risky_operation()
except Exception as e:
    logger.log(
        bucket="errors",
        data={
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "context": "user_signup"
        }
    )

logger.close()
```

### API Call Tracking

```python
from logflow import Logger
import time

logger = Logger(api_key="lf_...", project_id="...")

start = time.time()
response = requests.get("https://api.example.com/users")
duration = time.time() - start

logger.log(
    bucket="api_calls",
    data={
        "endpoint": "/users",
        "method": "GET",
        "status": response.status_code,
        "duration_ms": duration * 1000,
        "response_size": len(response.content)
    }
)

logger.close()
```

### User Activity Tracking

```python
from logflow import Logger

logger = Logger(api_key="lf_...", project_id="...")

# Track page views
logger.log(
    bucket="user_activity",
    data={
        "event": "page_view",
        "page": "/dashboard",
        "user_id": "user_123",
        "session_id": "sess_xyz",
        "referrer": "https://google.com"
    }
)

# Track feature usage
logger.log(
    bucket="user_activity",
    data={
        "event": "feature_used",
        "feature": "export_data",
        "user_id": "user_123",
        "format": "csv"
    }
)

logger.close()
```

### Multiple Projects

```python
from logflow import Logger

# Logger for production project
prod_logger = Logger(
    api_key="lf_prod_key",
    project_id="prod_project_id"
)

# Logger for development project
dev_logger = Logger(
    api_key="lf_dev_key",
    project_id="dev_project_id"
)

prod_logger.log(bucket="events", data={"env": "production"})
dev_logger.log(bucket="events", data={"env": "development"})

prod_logger.close()
dev_logger.close()
```

### Structured Logging

```python
from logflow import Logger
import datetime

logger = Logger(api_key="lf_...", project_id="...")

# E-commerce order tracking
logger.log(
    bucket="orders",
    data={
        "order_id": "ord_12345",
        "user_id": "user_789",
        "items": [
            {"sku": "PROD-001", "quantity": 2, "price": 29.99},
            {"sku": "PROD-002", "quantity": 1, "price": 49.99}
        ],
        "total": 109.97,
        "currency": "USD",
        "payment_method": "credit_card",
        "status": "completed",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
)

logger.close()
```

## Best Practices

### 1. Use Context Managers

Always use the context manager to ensure logs are properly flushed:

```python
with Logger(api_key="...", project_id="...") as logger:
    # Your logging code
    pass
# Automatically closes and flushes
```

### 2. Don't Create Logger Per Request

Create one logger instance and reuse it:

```python
# Good ✅
logger = Logger(api_key="...", project_id="...")

for i in range(100):
    logger.log(bucket="events", data={"count": i})

logger.close()

# Bad ❌
for i in range(100):
    with Logger(api_key="...", project_id="...") as logger:
        logger.log(bucket="events", data={"count": i})
```

### 3. Use Descriptive Bucket Names

Organize logs into logical buckets:

```python
logger.log(bucket="errors", data={...})           # Application errors
logger.log(bucket="user_activity", data={...})    # User interactions
logger.log(bucket="api_calls", data={...})        # External API tracking
logger.log(bucket="performance", data={...})      # Performance metrics
```

### 4. Include Context

Add relevant context to make logs useful:

```python
logger.log(
    bucket="errors",
    data={
        "error": str(e),
        "user_id": current_user.id,        # Who experienced it
        "request_id": request.id,          # Which request
        "environment": "production",       # Where it happened
        "timestamp": datetime.utcnow().isoformat()  # When
    }
)
```

### 5. Handle Sensitive Data

Don't log sensitive information:

```python
# Bad ❌
logger.log(bucket="auth", data={
    "password": user.password,        # Never log passwords
    "credit_card": user.cc_number    # Never log PII
})

# Good ✅
logger.log(bucket="auth", data={
    "user_id": user.id,
    "event": "login_success",
    "ip_address": hash(request.ip)   # Hash if needed
})
```

## Framework Integration

### Flask

```python
from flask import Flask, g
from logflow import Logger

app = Flask(__name__)

@app.before_request
def setup_logger():
    g.logger = Logger(api_key="...", project_id="...")

@app.after_request
def close_logger(response):
    if hasattr(g, 'logger'):
        g.logger.close()
    return response

@app.route('/api/users')
def get_users():
    g.logger.log(bucket="api", data={"endpoint": "/api/users"})
    return {"users": []}
```

### Django

```python
# middleware.py
from logflow import Logger

class LogFlowMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = Logger(api_key="...", project_id="...")
    
    def __call__(self, request):
        response = self.get_response(request)
        
        self.logger.log(
            bucket="requests",
            data={
                "path": request.path,
                "method": request.method,
                "status": response.status_code
            }
        )
        
        return response
```

### FastAPI

```python
from fastapi import FastAPI, Request
from logflow import Logger

app = FastAPI()
logger = Logger(api_key="...", project_id="...")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    
    logger.log(
        bucket="requests",
        data={
            "path": request.url.path,
            "method": request.method,
            "status": response.status_code
        }
    )
    
    return response
```

## Troubleshooting

### Logs Not Appearing?

1. **Check your API key**: Ensure it's valid and active
2. **Verify project ID**: Must match your LogFlow project
3. **Enable debug mode**: Set `debug=True` to see what's happening
4. **Check network**: Ensure your app can reach the LogFlow API
5. **Flush logs**: Call `logger.flush()` or `logger.close()` before exiting

### Debug Mode

```python
logger = Logger(
    api_key="...",
    project_id="...",
    debug=True  # Enable debug output
)

# Will print:
# [LogFlow] Background worker started
# [LogFlow] Queued log: user_activity
# [LogFlow] Sending batch of 1 logs
# [LogFlow] Batch sent successfully
```

### Manual Flush

```python
logger = Logger(api_key="...", project_id="...")

# Send logs immediately
logger.log(bucket="events", data={...})
logger.flush()  # Force send now

# Or close (which also flushes)
logger.close()
```

## API Reference

### `Logger(api_key, project_id, **options)`

Create a new Logger instance.

**Parameters:**
- `api_key` (str): Your LogFlow API key
- `project_id` (str): Your project ID
- `api_url` (str, optional): API URL (default: "http://localhost:8000")
- `batch_size` (int, optional): Logs per batch (default: 10)
- `flush_interval` (float, optional): Seconds between flushes (default: 5.0)
- `max_retries` (int, optional): Max retry attempts (default: 3)
- `debug` (bool, optional): Enable debug output (default: False)

### `logger.log(bucket, data)`

Send a log entry.

**Parameters:**
- `bucket` (str): Log category/bucket name
- `data` (dict): JSON-serializable log data

### `logger.flush()`

Force flush all pending logs immediately.

### `logger.close()`

Close the logger, flush pending logs, and stop background worker.

## Support

- Documentation: https://docs.logflow.dev
- GitHub: https://github.com/yourusername/logflow
- Issues: https://github.com/yourusername/logflow/issues

## License

MIT License - see LICENSE file for details
