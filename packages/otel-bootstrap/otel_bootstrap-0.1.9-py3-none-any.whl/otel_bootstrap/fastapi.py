# otel_bootstrap/fastapi.py
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def instrument_fastapi(app):
    FastAPIInstrumentor.instrument_app(app)
