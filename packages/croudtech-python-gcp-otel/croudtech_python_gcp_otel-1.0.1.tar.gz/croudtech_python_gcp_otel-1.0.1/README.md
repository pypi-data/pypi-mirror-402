# CroudTech Python GCP OpenTelemetry

OpenTelemetry configuration utilities for GCP Cloud Trace and Cloud Logging integration.

## Installation

```bash
# Install from PyPI
pip install croudtech-python-gcp-otel

# Install from GitHub
pip install git+https://github.com/CroudTech/croudtech-python-gcp-otel.git

# Install a specific version
pip install git+https://github.com/CroudTech/croudtech-python-gcp-otel.git@v1.0.0

# Install with Poetry
poetry add croudtech-python-gcp-otel

# Or from GitHub with Poetry
poetry add git+https://github.com/CroudTech/croudtech-python-gcp-otel.git
```

All instrumentations (Django, requests, psycopg2, logging) are included by default.

## Usage

### Basic Setup

```python
from croudtech_gcp_otel import configure_telemetry

# Configure using environment variables
configure_telemetry()
```

### Configuration via Environment Variables

- `GCP_PROJECT_ID` or `GOOGLE_CLOUD_PROJECT` - GCP project ID for Cloud Trace
- `GCP_REGION` - GCP region (default: europe-west2)
- `SERVICE_NAME` - Service name for tracing
- `SERVICE_VERSION` - Service version
- `K_SERVICE` - Cloud Run service name (auto-detected)
- `K_REVISION` - Cloud Run revision (auto-detected)

### Explicit Configuration

```python
from croudtech_gcp_otel import configure_telemetry, TelemetryConfig

config = TelemetryConfig(
    service_name="my-service",
    service_namespace="my-namespace",
    project_id="my-gcp-project",
    region="europe-west2",
    service_version="1.0.0",
    # Instrumentation flags (all default to True)
    instrument_django=True,
    instrument_requests=True,
    instrument_psycopg2=True,
    instrument_logging=True,
    # Psycopg2 SQL commenter options
    psycopg2_enable_commenter=True,
    psycopg2_commenter_options={
        "db_driver": True,
        "dbapi_threadsafety": True,
        "dbapi_level": True,
        "libpq_version": True,
        "driver_paramstyle": True,
    },
)
configure_telemetry(config)
```

### TelemetryConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `service_name` | str | `K_SERVICE` or `SERVICE_NAME` env var | Service name for tracing |
| `service_version` | str | `K_REVISION` or `SERVICE_VERSION` env var | Service version |
| `service_namespace` | str | `""` | Service namespace for grouping |
| `project_id` | str | `GCP_PROJECT_ID` or `GOOGLE_CLOUD_PROJECT` env var | GCP project ID |
| `region` | str | `GCP_REGION` env var or `europe-west2` | GCP region |
| `instrument_django` | bool | `True` | Enable Django auto-instrumentation |
| `instrument_requests` | bool | `True` | Enable requests library instrumentation |
| `instrument_psycopg2` | bool | `True` | Enable PostgreSQL instrumentation |
| `instrument_logging` | bool | `True` | Enable logging instrumentation |
| `psycopg2_enable_commenter` | bool | `True` | Add SQL comments with trace info |
| `psycopg2_commenter_options` | dict | See above | Configure SQL commenter fields |

### JSON Logging for GCP Cloud Logging

```python
from croudtech_gcp_otel import configure_logging
import logging

# Configure root logger with JSON formatting
configure_logging()

# Or with custom log level
configure_logging(level=logging.DEBUG)

# Or with explicit project ID for trace correlation
configure_logging(gcp_project_id="my-gcp-project")
```

Or use the formatter directly:

```python
import logging
from croudtech_gcp_otel import JSONFormatter

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter(
    gcp_project_id="my-gcp-project",  # For trace correlation URLs
    include_extra_fields=True,         # Include custom log record fields
))
logging.getLogger().addHandler(handler)
```

The JSON output includes:
- `timestamp`, `severity`, `message`, `logger`, `module`, `function`, `line`
- `exception` with type, message, and stacktrace (when applicable)
- `logging.googleapis.com/trace`, `logging.googleapis.com/spanId`, `logging.googleapis.com/trace_sampled` for Cloud Trace correlation

### Manual Span Creation

```python
from croudtech_gcp_otel import get_tracer, create_span_with_attributes

tracer = get_tracer(__name__)

with create_span_with_attributes(tracer, "my_operation", {"custom.attr": "value"}):
    # your code here
    pass
```

### GCP Resource Attributes

Get resource attributes for custom OpenTelemetry configurations:

```python
from croudtech_gcp_otel import get_gcp_resource_attributes, TelemetryConfig

# Using defaults from environment
attributes = get_gcp_resource_attributes()

# Or with explicit config
config = TelemetryConfig(service_name="my-service", project_id="my-project")
attributes = get_gcp_resource_attributes(config)

# Returns dict with: service.name, service.version, cloud.provider, cloud.platform,
# cloud.region, cloud.account.id, gcp.project_id, gcp.region, and Cloud Run
# specific attributes when running on Cloud Run
```

## Features

- **GCP Cloud Trace Integration**: Automatic export of traces to Cloud Trace
- **W3C Trace Context Propagation**: Standard distributed tracing headers
- **GCP Cloud Trace Propagation**: Native GCP trace header support
- **Auto-instrumentation**: Django, requests, psycopg2, and logging
- **JSON Logging**: GCP Cloud Logging compatible structured logs with trace correlation
- **App Hub Topology**: Resource attributes for service topology visualization
