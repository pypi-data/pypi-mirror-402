"""Custom logging formatters for GCP Cloud Logging compatibility."""

import json
import logging
import os
import traceback
from datetime import datetime, timezone
from typing import Optional


class JSONFormatter(logging.Formatter):
    """JSON formatter compatible with GCP Cloud Logging structured logs.

    This formatter produces JSON output that is compatible with GCP Cloud Logging
    and includes trace correlation fields when OpenTelemetry instrumentation is enabled.

    Usage:
        import logging
        from croudtech_gcp_otel.logging import JSONFormatter

        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logging.getLogger().addHandler(handler)
    """

    def __init__(
        self,
        *args,
        gcp_project_id: Optional[str] = None,
        include_extra_fields: bool = True,
        **kwargs
    ):
        """Initialize the JSON formatter.

        Args:
            gcp_project_id: GCP project ID for trace correlation. If not provided,
                           will be read from GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT env vars.
            include_extra_fields: Whether to include extra fields from log records.
        """
        super().__init__(*args, **kwargs)
        self.gcp_project_id = gcp_project_id or os.environ.get(
            "GCP_PROJECT_ID",
            os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        )
        self.include_extra_fields = include_extra_fields

    def _get_trace_context(self, record):
        """Get trace context from LoggingInstrumentor attributes or directly from current span.

        Returns tuple of (trace_id, span_id, trace_sampled) or (None, None, None) if not available.
        """
        # First, try to get from LoggingInstrumentor-injected attributes
        trace_id = getattr(record, "otelTraceID", None)
        span_id = getattr(record, "otelSpanID", None)
        trace_sampled = getattr(record, "otelTraceSampled", None)

        if trace_id:
            return trace_id, span_id, trace_sampled

        # Fallback: get trace context directly from current span
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            span_context = span.get_span_context() if span else None

            # Check if we have a valid, recording span
            if span_context and span_context.is_valid:
                return (
                    format(span_context.trace_id, '032x'),
                    format(span_context.span_id, '016x'),
                    span_context.trace_flags.sampled if hasattr(span_context.trace_flags, 'sampled') else False
                )
        except ImportError:
            pass
        except Exception:
            pass

        return None, None, None

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stacktrace": traceback.format_exception(*record.exc_info),
            }

        # Add trace context for correlation with Cloud Trace
        trace_id, span_id, trace_sampled = self._get_trace_context(record)

        if trace_id and self.gcp_project_id:
            log_entry["logging.googleapis.com/trace"] = (
                f"projects/{self.gcp_project_id}/traces/{trace_id}"
            )
        if span_id:
            log_entry["logging.googleapis.com/spanId"] = span_id
        if trace_sampled is not None:
            log_entry["logging.googleapis.com/trace_sampled"] = trace_sampled

        # Add any extra fields from the record
        if self.include_extra_fields:
            self._add_extra_fields(record, log_entry)

        return json.dumps(log_entry)

    def _add_extra_fields(self, record, log_entry):
        """Add extra fields from the log record to the entry."""
        excluded_keys = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "pathname", "process", "processName", "relativeCreated",
            "stack_info", "exc_info", "exc_text", "thread", "threadName",
            "otelTraceID", "otelSpanID", "otelTraceSampled", "otelServiceName",
            "message", "asctime", "taskName",
        }

        for key, value in record.__dict__.items():
            if key.startswith("extra_") or key in ("extra",):
                continue
            if key not in excluded_keys and not key.startswith("_"):
                try:
                    json.dumps(value)
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = f"<{type(value).__name__}>"


def configure_logging(
    level: int = logging.INFO,
    gcp_project_id: Optional[str] = None,
) -> None:
    """Configure the root logger with JSON formatting for GCP Cloud Logging.

    Args:
        level: Logging level (default: INFO)
        gcp_project_id: GCP project ID for trace correlation
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new JSON handler
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter(gcp_project_id=gcp_project_id))
    root_logger.addHandler(handler)
