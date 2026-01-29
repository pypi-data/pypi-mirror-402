# FailSense Python SDK

[![PyPI version](https://badge.fury.io/py/failsense.svg)](https://badge.fury.io/py/failsense)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Error tracking and LLM monitoring for Python applications.

## Features

- ✅ **Error Tracking** - Automatic exception capture with stack traces
- ✅ **Monitor Tracking** - Cron job and uptime monitoring
- ✅ **AI Tracer** - LLM API call monitoring (tokens, cost, latency)
- ✅ **Session Replay** - User session recording
- ✅ **Breadcrumbs** - Track user actions before errors
- ✅ **Zero Config** - Works out of the box

## Installation

```bash
pip install failsense
```

## Quick Start

### 1. Get Your API Key

Sign up at [failsense.com](https://failsense.com) and get your API key from Settings.

### 2. Initialize the SDK

```python
from failsense import Client

fs = Client(
    dsn="https://api.failsense.com",
    api_key="fs_live_..."  # Your API key
)
```

### 3. Track Errors

```python
try:
    1 / 0
except Exception:
    fs.capture_exception()
```

### 4. Monitor LLM Calls

```python
from openai import OpenAI

# Wrap your LLM client
raw_client = OpenAI(api_key="sk-...")
client = fs.monitor(raw_client, tracer_id=1)

# Use normally - automatically tracked!
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Usage Examples

### Error Tracking

```python
from failsense import Client

fs = Client(dsn="https://api.failsense.com", api_key="fs_live_...")

# Automatic exception capture
try:
    risky_operation()
except Exception:
    fs.capture_exception()

# With additional context
try:
    process_user(user_id=123)
except Exception:
    fs.capture_exception(context={"user_id": 123, "action": "process"})
```

### Breadcrumbs

```python
# Track user actions
fs.add_breadcrumb("navigation", "User clicked checkout")
fs.add_breadcrumb("http", "API call to /payment", data={"amount": 99.99})

# Breadcrumbs are automatically attached to errors
try:
    process_payment()
except Exception:
    fs.capture_exception()  # Includes breadcrumbs
```

### Monitor Tracking

```python
# Cron job monitoring
from failsense import Client

fs = Client(dsn="https://api.failsense.com", api_key="fs_live_...")

def daily_backup():
    try:
        backup_database()
        fs.check_in_monitor(monitor_id=1, status="ok")
    except Exception as e:
        fs.check_in_monitor(monitor_id=1, status="error", metadata={"error": str(e)})
```

### AI Tracer (LLM Monitoring)

```python
from failsense import Client
from openai import OpenAI

fs = Client(dsn="https://api.failsense.com", api_key="fs_live_...")

# Wrap your LLM client
raw_client = OpenAI(api_key="sk-...")
client = fs.monitor(raw_client, tracer_id=1)

# All calls are automatically tracked
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Explain quantum physics"}]
)

# Tracks:
# - Tokens used (input/output)
# - Latency
# - Cost estimation
# - Errors (with full prompt for debugging)
```

## Configuration

### DSN Options

```python
# Production
fs = Client(dsn="https://api.failsense.com", api_key="fs_live_...")

# Self-hosted
fs = Client(dsn="https://failsense.yourcompany.com", api_key="...")

# Local development
fs = Client(dsn="http://localhost:8000", api_key="...")
```

### Graceful Shutdown

```python
import atexit

fs = Client(dsn="...", api_key="...")

# Flush pending events on exit
atexit.register(fs.close)
```

## Framework Integration

### Django

```python
# settings.py
FAILSENSE_DSN = "https://api.failsense.com"
FAILSENSE_API_KEY = "fs_live_..."

# middleware.py
from failsense import Client

fs = Client(dsn=settings.FAILSENSE_DSN, api_key=settings.FAILSENSE_API_KEY)

class FailsenseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception:
            fs.capture_exception(context={"path": request.path})
            raise
```

### Flask

```python
from flask import Flask
from failsense import Client

app = Flask(__name__)
fs = Client(dsn="https://api.failsense.com", api_key="fs_live_...")

@app.errorhandler(Exception)
def handle_exception(e):
    fs.capture_exception()
    return "Internal Server Error", 500
```

### FastAPI

```python
from fastapi import FastAPI, Request
from failsense import Client

app = FastAPI()
fs = Client(dsn="https://api.failsense.com", api_key="fs_live_...")

@app.middleware("http")
async def failsense_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception:
        fs.capture_exception(context={"path": request.url.path})
        raise
```

## Supported LLM Providers

- ✅ OpenAI (GPT-3.5, GPT-4)
- ✅ Anthropic (Claude 3)
- ✅ Google (Gemini)
- ✅ Any provider with `chat.completions.create()` interface

## Requirements

- Python 3.8 or higher
- `requests>=2.25.0`

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **Homepage**: https://failsense.com
- **Documentation**: https://docs.failsense.com
- **GitHub**: https://github.com/failsense/failsense-python
- **PyPI**: https://pypi.org/project/failsense
- **Support**: support@failsense.com

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

### 0.1.0 (2026-01-17)

- Initial release
- Error tracking
- Monitor tracking
- AI Tracer (LLM monitoring)
- Breadcrumbs
- Session replay support
