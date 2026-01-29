# otel-bootstrap

Minimal OpenTelemetry bootstrap for Python services.

## Features
- FastAPI tracing
- SQLAlchemy (sync & async)
- Redis (sync & async)
- HTTP / MinIO
- Trace ↔ Log correlation

## Usage

```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from otel_bootstrap import setup_otel, OtelSettings

app = FastAPI()
engine = create_async_engine("postgresql+asyncpg://...")

setup_otel(
    settings=OtelSettings(service_name="example"),
    fastapi_app=app,
    sqlalchemy_engine=engine,
)
