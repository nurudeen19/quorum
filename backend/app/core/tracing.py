"""OpenTelemetry tracing setup for FastAPI app."""
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from app.config import get_settings, AppSettings


def setup_tracing(settings: AppSettings | None = None) -> None:
    """Configure OpenTelemetry tracing using AppSettings."""
    if settings is None:
        settings = get_settings().app
    
    provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: settings.otel_service_name})
    )
    trace.set_tracer_provider(provider)
    
    try:
        if settings.otel_exporter_otlp_endpoint:
            exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        else:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(f"Failed to setup OTLP exporter, using console: {exc}")
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
