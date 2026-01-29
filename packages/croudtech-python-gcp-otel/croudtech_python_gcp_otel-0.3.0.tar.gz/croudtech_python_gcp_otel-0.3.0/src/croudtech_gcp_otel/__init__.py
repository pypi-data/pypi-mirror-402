"""CroudTech GCP OpenTelemetry utilities.

This package provides OpenTelemetry configuration utilities for GCP Cloud Trace
and Cloud Logging integration.

Usage:
    from croudtech_gcp_otel import configure_telemetry, TelemetryConfig

    # Simple setup using environment variables
    configure_telemetry()

    # Or with explicit configuration
    config = TelemetryConfig(
        service_name="my-service",
        service_namespace="my-namespace",
        project_id="my-gcp-project",
    )
    configure_telemetry(config)
"""

from croudtech_gcp_otel.telemetry import (
    TelemetryConfig,
    configure_telemetry,
    get_gcp_resource_attributes,
    get_tracer,
    create_span_with_attributes,
)
from croudtech_gcp_otel.logging import (
    JSONFormatter,
    configure_logging,
)

__version__ = "0.1.0"

__all__ = [
    # Telemetry
    "TelemetryConfig",
    "configure_telemetry",
    "get_gcp_resource_attributes",
    "get_tracer",
    "create_span_with_attributes",
    # Logging
    "JSONFormatter",
    "configure_logging",
]
