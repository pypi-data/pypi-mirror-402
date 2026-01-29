# CroudTech Python GCP OpenTelemetry

OpenTelemetry configuration utilities for GCP Cloud Trace and Cloud Logging integration.

## Installation

```bash
# Install from GitHub with pip
pip install git+https://github.com/CroudTech/croudtech-python-gcp-otel.git

# Install a specific version
pip install git+https://github.com/CroudTech/croudtech-python-gcp-otel.git@v0.1.0

# Install with Poetry
poetry add git+https://github.com/CroudTech/croudtech-python-gcp-otel.git

# Install a specific version with Poetry
poetry add git+https://github.com/CroudTech/croudtech-python-gcp-otel.git#v0.1.0
```

### Optional Dependencies

Install with extras for auto-instrumentation:

```bash
# With pip
pip install "croudtech-python-gcp-otel[all] @ git+https://github.com/CroudTech/croudtech-python-gcp-otel.git"

# Or specific instrumentations
pip install "croudtech-python-gcp-otel[django,requests] @ git+https://github.com/CroudTech/croudtech-python-gcp-otel.git"
```

Available extras: `django`, `requests`, `psycopg2`, `logging`, `all`

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
    instrument_django=True,
    instrument_requests=True,
    instrument_psycopg2=True,
    instrument_logging=True,
)
configure_telemetry(config)
```

### JSON Logging for GCP Cloud Logging

```python
from croudtech_gcp_otel import configure_logging

# Configure root logger with JSON formatting
configure_logging()
```

Or use the formatter directly:

```python
import logging
from croudtech_gcp_otel import JSONFormatter

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger().addHandler(handler)
```

### Manual Span Creation

```python
from croudtech_gcp_otel import get_tracer, create_span_with_attributes

tracer = get_tracer(__name__)

with create_span_with_attributes(tracer, "my_operation", {"custom.attr": "value"}):
    # your code here
    pass
```

## Features

- **GCP Cloud Trace Integration**: Automatic export of traces to Cloud Trace
- **W3C Trace Context Propagation**: Standard distributed tracing headers
- **GCP Cloud Trace Propagation**: Native GCP trace header support
- **Auto-instrumentation**: Django, requests, psycopg2, and logging
- **JSON Logging**: GCP Cloud Logging compatible structured logs with trace correlation
- **App Hub Topology**: Resource attributes for service topology visualization
