# otel_bootstrap/__init__.py
from ._state import _otel_initialized
from .config import OtelSettings
from .tracer import setup_tracer
from .fastapi import instrument_fastapi
from .grpc import instrument_grpc
from .http import instrument_http_clients
from .postgres import instrument_postgres
from .redis import instrument_redis
from .logging import setup_logging


def setup_otel(
    *,
    settings: OtelSettings,
    fastapi_app=None,
    sqlalchemy_engine=None,
):
    global _otel_initialized

    if _otel_initialized:
        return
    _otel_initialized = True
    setup_tracer(settings)
    setup_logging()

    if settings.enable_fastapi and fastapi_app:
        instrument_fastapi(fastapi_app)

    if settings.enable_grpc:
        instrument_grpc()

    instrument_http_clients()
    instrument_redis()

    if sqlalchemy_engine:
        instrument_postgres(sqlalchemy_engine)
