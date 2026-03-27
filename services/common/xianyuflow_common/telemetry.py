"""Telemetry configuration for logging and tracing."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from opentelemetry.trace import Tracer


def configure_structlog(log_level: str = "INFO") -> None:
    """Configure structlog for structured logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name.

    Returns:
        BoundLogger: Structured logger instance.
    """
    return structlog.get_logger(name)


def get_tracer(name: str) -> Tracer:
    """Get an OpenTelemetry tracer instance.

    Args:
        name: Tracer name.

    Returns:
        Tracer: OpenTelemetry tracer instance.
    """
    from opentelemetry import trace

    return trace.get_tracer(name)


def configure_opentelemetry(
    service_name: str,
    service_version: str = "0.1.0",
    exporter_endpoint: str | None = None,
) -> None:
    """Configure OpenTelemetry tracing.

    Args:
        service_name: Name of the service.
        service_version: Version of the service.
        exporter_endpoint: Optional OTLP exporter endpoint.
    """
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    resource = Resource(
        attributes={
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    provider = TracerProvider(resource=resource)

    if exporter_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=exporter_endpoint)
    else:
        exporter = ConsoleSpanExporter()

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
