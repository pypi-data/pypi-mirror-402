"""OpenTelemetry configuration for GCP Cloud Trace and App Hub topology."""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Module-level flag to prevent double initialization
_telemetry_configured = False


@dataclass
class TelemetryConfig:
    """Configuration for OpenTelemetry setup."""

    service_name: str = ""
    service_version: str = "1.0.0"
    service_namespace: str = ""
    project_id: str = ""
    region: str = "europe-west2"

    # Instrumentation flags
    instrument_django: bool = True
    instrument_requests: bool = True
    instrument_psycopg2: bool = True
    instrument_logging: bool = True

    # Psycopg2 commenter options
    psycopg2_enable_commenter: bool = True
    psycopg2_commenter_options: dict = field(default_factory=lambda: {
        "db_driver": True,
        "dbapi_threadsafety": True,
        "dbapi_level": True,
        "libpq_version": True,
        "driver_paramstyle": True,
    })

    def __post_init__(self):
        """Resolve configuration from environment if not provided."""
        if not self.project_id:
            self.project_id = os.environ.get(
                "GCP_PROJECT_ID",
                os.environ.get("GOOGLE_CLOUD_PROJECT", "")
            )

        if not self.region:
            self.region = os.environ.get("GCP_REGION", "europe-west2")

        # Cloud Run environment detection
        k_service = os.environ.get("K_SERVICE", "")
        k_revision = os.environ.get("K_REVISION", "")

        if not self.service_name:
            self.service_name = k_service or os.environ.get("SERVICE_NAME", "unknown-service")

        if not self.service_version or self.service_version == "1.0.0":
            if k_revision:
                self.service_version = k_revision
            else:
                self.service_version = os.environ.get("SERVICE_VERSION", "1.0.0")


def get_gcp_resource_attributes(config: Optional[TelemetryConfig] = None):
    """
    Get GCP-specific resource attributes for App Hub topology visualization.

    These attributes help App Hub understand the relationships between services
    and build accurate topology maps.

    Args:
        config: Optional TelemetryConfig. If not provided, creates one from environment.

    Returns:
        Dictionary of resource attributes.
    """
    from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION

    if config is None:
        config = TelemetryConfig()

    k_service = os.environ.get("K_SERVICE", "")
    k_revision = os.environ.get("K_REVISION", "")

    attributes = {
        SERVICE_NAME: config.service_name,
        SERVICE_VERSION: config.service_version,
        # GCP-specific attributes for topology
        "cloud.provider": "gcp",
        "cloud.platform": "gcp_cloud_run",
        "cloud.region": config.region,
        "cloud.account.id": config.project_id,
        # Cloud Run specific attributes
        "gcp.project_id": config.project_id,
        "gcp.region": config.region,
    }

    # Add service namespace if provided
    if config.service_namespace:
        attributes["service.namespace"] = config.service_namespace

    # Add Cloud Run specific attributes if available
    if k_service:
        attributes["cloud_run.service_name"] = k_service
        attributes["faas.name"] = k_service

    if k_revision:
        attributes["cloud_run.revision_name"] = k_revision
        attributes["faas.version"] = k_revision

    return attributes


def configure_telemetry(config: Optional[TelemetryConfig] = None):
    """
    Configure OpenTelemetry with GCP exporters for Cloud Trace and App Hub topology.

    This configuration enables:
    - Distributed tracing with Cloud Trace
    - Service topology visualization in App Hub
    - Auto-instrumentation for Django, PostgreSQL, requests, and logging

    This function is idempotent - calling it multiple times is safe and will
    only configure telemetry once.

    Args:
        config: Optional TelemetryConfig. If not provided, creates one from environment.
    """
    global _telemetry_configured

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import ALWAYS_ON
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.composite import CompositePropagator
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.baggage.propagation import W3CBaggagePropagator

    # Check if already configured (both our flag and OTel's internal state)
    if _telemetry_configured:
        logger.debug("Telemetry already configured (flag), skipping")
        return

    # Also check if a TracerProvider is already set (handles multi-process scenarios)
    current_provider = trace.get_tracer_provider()
    if isinstance(current_provider, TracerProvider):
        logger.debug("TracerProvider already set, skipping configuration")
        _telemetry_configured = True
        return

    if config is None:
        config = TelemetryConfig()

    # Create resource with GCP attributes
    resource = Resource(attributes=get_gcp_resource_attributes(config))

    # Create tracer provider with explicit ALWAYS_ON sampling to ensure all traces are captured
    provider = TracerProvider(resource=resource, sampler=ALWAYS_ON)

    # Configure GCP Cloud Trace exporter if running in GCP
    if config.project_id:
        try:
            from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

            cloud_trace_exporter = CloudTraceSpanExporter(project_id=config.project_id)
            provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
            logger.info(f"Cloud Trace exporter configured for project: {config.project_id}")
        except ImportError as e:
            logger.warning(f"Cloud Trace exporter not available: {e}")
        except Exception as e:
            logger.error(f"Failed to configure Cloud Trace exporter: {e}")

    # Set the tracer provider
    try:
        trace.set_tracer_provider(provider)
    except Exception as e:
        # Provider already set (e.g., by another call or auto-instrumentation)
        logger.debug(f"TracerProvider already set: {e}")
        _telemetry_configured = True
        return

    # Configure trace context propagation for distributed tracing
    # Include both W3C and GCP Cloud Trace propagators for broad compatibility
    propagators = [
        TraceContextTextMapPropagator(),
        W3CBaggagePropagator(),
    ]

    # Add GCP Cloud Trace propagator for native Cloud Trace integration
    try:
        from opentelemetry.propagators.cloud_trace_propagator import CloudTraceFormatPropagator
        propagators.append(CloudTraceFormatPropagator())
        logger.info("GCP Cloud Trace propagator enabled")
    except ImportError:
        logger.debug("GCP Cloud Trace propagator not available, using W3C only")

    set_global_textmap(CompositePropagator(propagators))

    # Instrument Django
    if config.instrument_django:
        try:
            from opentelemetry.instrumentation.django import DjangoInstrumentor
            DjangoInstrumentor().instrument()
            logger.info("Django instrumentation enabled")
        except ImportError:
            logger.debug("Django instrumentation not available")
        except Exception as e:
            logger.warning(f"Django instrumentation failed: {e}")

    # Instrument requests library for outgoing HTTP calls
    if config.instrument_requests:
        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor
            RequestsInstrumentor().instrument()
            logger.info("Requests instrumentation enabled")
        except ImportError:
            logger.debug("Requests instrumentation not available")
        except Exception as e:
            logger.warning(f"Requests instrumentation failed: {e}")

    # Instrument PostgreSQL for database topology
    if config.instrument_psycopg2:
        try:
            from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
            Psycopg2Instrumentor().instrument(
                enable_commenter=config.psycopg2_enable_commenter,
                commenter_options=config.psycopg2_commenter_options,
            )
            logger.info("PostgreSQL instrumentation enabled")
        except ImportError:
            logger.debug("PostgreSQL instrumentation not available")
        except Exception as e:
            logger.warning(f"PostgreSQL instrumentation failed: {e}")

    # Instrument logging to correlate logs with traces
    # Note: set_logging_format=False ensures trace context is injected as record attributes
    # (otelTraceID, otelSpanID, otelTraceSampled) rather than modifying the format string.
    # The JSONFormatter in logging.py reads these attributes to add trace correlation.
    if config.instrument_logging:
        try:
            from opentelemetry.instrumentation.logging import LoggingInstrumentor
            LoggingInstrumentor().instrument(set_logging_format=False)
            logger.info("Logging instrumentation enabled")
        except ImportError:
            logger.debug("Logging instrumentation not available")
        except Exception as e:
            logger.warning(f"Logging instrumentation failed: {e}")

    _telemetry_configured = True
    logger.info("OpenTelemetry configuration complete")


def get_tracer(name: str = __name__):
    """Get a tracer instance for manual span creation."""
    from opentelemetry import trace
    return trace.get_tracer(name)


def create_span_with_attributes(tracer, name: str, attributes: dict = None):
    """
    Create a span with additional attributes for topology visualization.

    Usage:
        tracer = get_tracer(__name__)
        with create_span_with_attributes(tracer, "my_operation", {"custom.attribute": "value"}):
            # do work
            pass
    """
    span_attributes = attributes or {}
    return tracer.start_as_current_span(name, attributes=span_attributes)
