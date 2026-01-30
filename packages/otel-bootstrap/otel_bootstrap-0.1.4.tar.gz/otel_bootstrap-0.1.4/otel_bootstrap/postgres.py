# otel_bootstrap/postgres.py
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

def instrument_postgres(engine):
    """
    engine: Engine | AsyncEngine
    """
    if isinstance(engine, AsyncEngine):
        target_engine = engine.sync_engine
    elif isinstance(engine, Engine):
        target_engine = engine
    else:
        raise TypeError("engine must be Engine or AsyncEngine")

    SQLAlchemyInstrumentor().instrument(
        engine=target_engine,
        enable_commenter=True,
        commenter_options={
            "db_driver": True,
            "dbapi_threadsafety": True,
        },
    )
