# otel_bootstrap/config.py
import os


try:
    # Pydantic v2
    from pydantic_settings import BaseSettings
    from pydantic import Field
    from pydantic_settings import SettingsConfigDict

    PYDANTIC_V2 = True
except ImportError:
    # Pydantic v1
    from pydantic import BaseSettings, Field

    PYDANTIC_V2 = False


def get_env(name, default):
    return os.getenv(name) or default


class OtelSettings(BaseSettings):
    service_name: str = Field(default=get_env("APP_NAME", "app"))
    service_version: str = Field(default="0.1.0")

    otel_endpoint: str = Field(
        default=get_env(
            "OTEL_ENDPOINT", "http://localhost:4317",
        )
    )
    otel_auth_header: str = Field(default=get_env("OTEL_AUTH_HEADER", ""))

    enable_fastapi: bool = True
    enable_grpc: bool = True
    enable_http_client: bool = True
