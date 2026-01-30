# otel_bootstrap/grpc.py
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer

def instrument_grpc():
    GrpcInstrumentorServer().instrument()
