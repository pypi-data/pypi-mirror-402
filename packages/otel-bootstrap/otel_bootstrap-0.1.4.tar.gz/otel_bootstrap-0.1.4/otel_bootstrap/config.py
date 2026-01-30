# otel_bootstrap/config.py
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


class OtelSettings(BaseSettings):
    service_name: str = Field(default="app")
    service_version: str = Field(default="0.1.0")

    otel_endpoint: str = Field(default="http://localhost:4317")
    otel_auth_header: str = Field(default="")  

    otel_protocol: str = Field(default="grpc")

    enable_fastapi: bool = True
    enable_grpc: bool = True
    enable_http_client: bool = True

    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_prefix="OTEL_",
            case_sensitive=False,
        )
    else:
        class Config:
            env_prefix = "OTEL_"
            case_sensitive = False
