<div align="center">

# Trazelet

**A Lightweight, Zero-Configuration Observability Middleware for Python Backends**

*Seamlessly integrates with FastAPI, Django, and Flask to deliver instant HTTP and API performance insights*

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/) [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Purpose](#-built-with-purpose) • [Contributing](/CONTRIBUTING.md)

</div>

---

## 🎯 What is Trazelet?

**Trazelet** is a high-performance, open-source Python **plug-and-play middleware library** that provides backend developers with **instant HTTP and API performance analytics**. It delivers immediate visibility into request latency without the complexity or overhead of traditional enterprise APM tools, and integrates seamlessly with Python web frameworks with zero configuration.

### The Problem It Solves

Most developers don't know their API is slow until a user complains. Enterprise tools (like New Relic, Datadog) are too expensive or hard to set up for small-to-medium projects. Trazelet fills this gap by being **local, private, and lightweight**.

### Why Trazelet?

- 🚀 **Near-Zero Overhead**: Non-blocking design with <0.2ms average latency impact
- 🔒 **Privacy-First**: All data stays on your machine. No cloud, no external services
- 🎯 **Zero Configuration**: Works out of the box with sensible defaults
- 🔌 **Framework Agnostic**: Works seamlessly with FastAPI, Django, and Flask
- ⚡ **Production-Ready**: Thread-safe, battle-tested architecture
- 📊 **Built-in Performance Analytics**: Actionable HTTP and API performance metrics out of the box
- 💻 **Modern TUI Interface**: Access real-time and historical analytics through a Rich-powered terminal UI

---

## ✨ Features

### Core Capabilities

- ✅ **Automatic Request Tracking**: Captures latency, status codes, and API paths
- ✅ **Non-Blocking Architecture**: Queue-based buffering ensures zero impact on response times
- ✅ **Batch Processing**: Configurable batching for high-performance metric storage
- ✅ **Thread-Safe**: Verified with 100+ concurrent operations
- ✅ **Invisible Middleware**: Never crashes your application, graceful error handling
- ✅ **Local Storage**: SQLite (default) or PostgreSQL support
- ✅ **Route Normalization**: Automatically normalizes dynamic paths (`/user/123` → `/user/<id>`)

### Framework Support

- ✅ **FastAPI**: Clean ASGI middleware integration
- ✅ **Django**: Standard middleware pattern
- ✅ **Flask**: Proper request tracking with `g` object

### Analytics & TUI Capabilities

- 📊 **Real-time Performance Reports**: Instant health overviews and detailed metric breakdowns via CLI.
- 📈 **Endpoint Health Grading**: Automated A/B/C/D grading for API endpoints based on performance.
- 🐢 **Anomaly Detection**: Quickly pinpoint slowest or most error-prone endpoints.
- 🎨 **Rich Command-Line Interface**: Interactive terminal output with tables, panels, and color-coding, powered by `Rich`.
- 📋 **Flexible Output Formats**: View analytics in human-readable tables, compact views, or machine-parseable JSON.

### Core Performance Metrics

- **Capture Latency**: ~0.12ms average (non-blocking) ensures minimal impact.
- **Concurrent Operations**: Thread-safe design, verified with 100+ concurrent captures.
- **Background Database Writes**: Asynchronous processing with zero impact on the request path.
- **Minimal Memory Footprint**: Efficient queue-based buffering for low resource consumption.

---

## 🚀 Quick Start

### Installation

```bash
# Core installation
pip install trazelet
```

### Basic Usage

#### FastAPI

```python
from fastapi import FastAPI
from trazelet.integrations.fastapi import FastAPIMiddleware
import trazelet

# Initialize Trazelet (uses SQLite by default)
trazelet.init()

app = FastAPI()
app.add_middleware(FastAPIMiddleware)

@app.get("/")
def read_root():
    return {"message": "Hello World"}
```

#### Django

```python
# settings.py
MIDDLEWARE = [
    # ... other middleware ...
    "trazelet.integrations.django.DjangoMiddleware",
]

# Initialize Trazelet
import trazelet
trazelet.init()
```

#### Flask

```python
from flask import Flask
from trazelet.integrations.flask import FlaskMiddleware
import trazelet

trazelet.init()

app = Flask(__name__)
app.wsgi_app = FlaskMiddleware(app=app)

@app.route("/")
def hello():
    return "Hello World!"
```

### Custom Configuration

```python
import trazelet

# Custom database and settings
trazelet.init(
    db_config={
        "db_url": "postgresql+psycopg2://user:pass@localhost:5432/trazelet",
        "echo": False
    },
    batch_size=100,           # Batch size for bulk inserts
    flush_interval=5.0,        # Flush interval in seconds
    max_workers=3,            # Background worker threads
    use_bulk_mode=True,       # Enable bulk insert mode
    logger_level="INFO"       # Logging level
    BUKCET_THRESHOLDS= [      # Set bucket threashold to classify for histogram in db
	25, 50, 100,
	200, 500, 1000,
	1500, 3000, 5000
    ]
)
```

---

## 📊 What Gets Tracked?

Trazelet automatically captures:

- **API Path**: Normalized route patterns (e.g., `/user/<id>` instead of `/user/123`)
- **Latency**: Request start/end times and elapsed duration
- **Status Codes**: HTTP response status codes
- **Framework**: Identifies which framework handled the request
- **Timestamps**: Precise request/response timestamps

**Example Metrics:**

```
/api/users/123     | 45ms  | 200 | FastAPI | 2025-01-15 10:30:00
/api/users/456     | 120ms | 200 | FastAPI | 2025-01-15 10:30:01
/api/orders/789    | 15ms  | 404 | FastAPI | 2025-01-15 10:30:02
```

---

## 🏗️ Architecture

### Design Principles

1. **Non-Blocking**: All database operations happen in background threads
2. **Thread-Safe**: Uses `ThreadPoolExecutor` and thread-safe queues
3. **Invisible**: Never crashes your application, all errors are caught and logged
4. **Efficient**: Batch processing reduces database overhead

### How It Works

```
Request → Middleware → Queue → Background Worker → Database
         (<0.2ms)    (O(1))   (Async)            (Batched)
```

1. **Request arrives** → Middleware captures start time
2. **Response sent** → Middleware captures end time and queues metric
3. **Background worker** → Processes queue in batches
4. **Database** → Bulk inserts for performance

---

## 📊 Real-time Analytics & TUI

Trazelet isn't just about capturing data; it's about making that data actionable. The **Trazelet Text User Interface (TUI)**, powered by [`src/trazelet/tui/app.py`](src/trazelet/tui/app.py), provides a rich, interactive command-line experience to instantly visualize and analyze your API's performance.

Leveraging the robust **Analytics Engine** described in the [Architecture Report](docs/architecture_report.md), the TUI transforms raw metrics into comprehensive, human-readable reports right in your terminal.

### Key TUI Features:

- ⚡ **Instant Performance Insights**: Get real-time health overviews and detailed metric breakdowns.
- 🎨 **Rich, Interactive Output**: Uses `Rich` library for color-coded tables, panels, and progress spinners.
- 🎯 **Endpoint-Level Granularity**: Analyze individual endpoint performance (latency, errors, throughput, Apdex).
- 🔍 **Anomaly Detection**: Quickly identify slowest or most error-prone endpoints.
- 📋 **Flexible Reporting**: View metrics in detailed tables, compact summaries, or JSON for programmatic use.

### ⚙️ Configuring Database Connection via CLI

The `trazelet configure-db` command sets up your database connection following a strict precedence order:

1. **`TRACELET_DB_URL`**: Highest priority, used if set in your environment.
2. **`DATABASE_URL`**: Used if present, after prompting for confirmation.
3. **Custom Environment Variable**: Use `--env-var <NAME>` to save an environment variable name in `~/.trazelet/config.json`. Trazelet will read the actual URL from `os.environ[NAME]` on subsequent runs.
4. **Default SQLite**: If no other sources are found, Trazelet defaults to an internal SQLite database (`sqlite:///trazelet.db`).

Use `trazelet configure-db --reset` to clear any previously saved custom environment variable name and re-evaluate the configuration.

### Available Commands:

The Trazelet CLI (exposed via the `trazelet` command) offers the following powerful commands:

- Get an operational health overview of all monitored endpoints, including health grades and distribution.

  - [`trazelet status`](src/trazelet/tui/app.py:285):

    ```bash
    trazelet status -d last_24h
    ```
- Dive into detailed analytics for all or specific endpoints, showing percentiles (P50, P95, P99), error rates, throughput, and Apdex scores.

  - [`trazelet describe`](src/trazelet/tui/app.py:377):

  ```bash
  trazelet describe -d "7 days" --sort p99 -f json
  ```
- Highlight performance anomalies by listing the top N slowest or most error-prone endpoints.

  - [`trazelet top`](src/trazelet/tui/app.py:463):

  ```bash
  trazelet top -m error -n 5
  ```
- View a comprehensive list of all active endpoints being monitored, with filtering options by framework or HTTP method.

  - [`trazelet list`](src/trazelet/tui/app.py:554):

  ```bash
  trazelet list --framework fastapi
  ```

---

## 📖 Documentation

### Configuration Options

| Parameter          | Type  | Default    | Description                                                         |
| ------------------ | ----- | ---------- | ------------------------------------------------------------------- |
| `db_config`      | dict  | `None`   | Database configuration (uses SQLite if not provided)                |
| `enabled`        | bool  | `True`   | Enable/disable Trazelet tracking                                    |
| `batch_size`     | int   | `50`     | Number of metrics to batch before flushing                          |
| `flush_interval` | float | `5.0`    | Maximum seconds to wait before flushing queue data to DB            |
| `max_workers`    | int   | `1`      | Background worker threads (1 for SQLite, configurable for Postgres) |
| `use_bulk_mode`  | bool  | `True`   | Enable bulk insert mode for performance                             |
| `logger_level`   | str   | `"INFO"` | Logging level: DEBUG, INFO, WARNING, ERROR                          |

---

### Database Configuration

#### SQLite (Default)

```python
trazelet.init()  # Uses SQLite automatically
```

#### PostgreSQL

```python
trazelet.init(
    db_config={
        "db_url": "postgresql+psycopg2://user:password@localhost:5432/dbname",
        "echo": False
    },
    max_workers=3  # Multiple workers for better throughput
)
```

### Advanced Usage

#### Disable Trazelet Temporarily

```python
trazelet.init(enabled=False)  # Disables tracking without removing middleware
```

#### Custom Logging

```python
trazelet.init(logger_level="DEBUG")  # More verbose logging
```

#### Manual Flush

```python
from trazelet.core.engine import get_engine

engine = get_engine()
engine.flush_buffer()  # Manually flush queued metrics
```

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

---

## 💡 Built With Purpose

- **The Vision:** A high-velocity performance tracker tailored for the modern era of API wrappers and micro-services.
- **Privacy by Design:** Instant analytics that stay in your environment. We provide the logic; you keep the data.
- **Zero-Config Core:** Works out of the box with sensible defaults, while offering minimal config for those who need it.
- **Flexible Persistence:** Plug into your existing **PostgreSQL** for production or stay lightweight with **SQLite** by default.
- **The Community:** Built for the developers who prioritize lean, efficient tools. Thank you to everyone helping us keep this project focused and fast!

---

## 📚 Additional Resources

- [Architecture report](docs/architecture_report.md) - Comprehensive technical audit
- [Testing report](docs/testing_report.md) - Test suite documentation
- [Tracker](docs/Tracker.md) - Development roadmap and feature tracking	

---

## 💬 Support

- **Issues**: [GitHub Issues](./issues)
- **Discussions**: [GitHub Discussions](../../discussions)

---

<div align="center">

[⭐ Star us on GitHub](.) • [📖 Documentation](docs/architecture_report.md) • [🐛 Report Bug](../../issues)

</div>
