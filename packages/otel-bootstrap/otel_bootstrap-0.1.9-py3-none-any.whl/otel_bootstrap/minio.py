# otel_bootstrap/http.py
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def instrument_http_clients():
    """
    - requests (sync)
    - httpx (async + sync)
    """
    RequestsInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
