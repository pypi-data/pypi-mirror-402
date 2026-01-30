# otel_bootstrap/redis.py
from opentelemetry.instrumentation.redis import RedisInstrumentor

def instrument_redis():
    """
    Hỗ trợ:
    - redis.Redis
    - redis.asyncio.Redis
    """
    RedisInstrumentor().instrument()
