# otel_bootstrap/tracer.py
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


from .config import OtelSettings


def setup_tracer(settings: OtelSettings):
    provider = TracerProvider(
        resource=Resource.create({
            "service.name": settings.service_name,
            "service.version": settings.service_version,
        })
    )
    
    exporter = OTLPSpanExporter(
        endpoint=settings.otel_endpoint,
        headers={
            "Authorization": f"Basic {settings.otel_access_key}",
        },
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
