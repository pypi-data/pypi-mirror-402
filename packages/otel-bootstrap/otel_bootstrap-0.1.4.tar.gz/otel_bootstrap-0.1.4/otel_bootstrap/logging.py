# otel_bootstrap/logging.py
import logging
from opentelemetry.trace import get_current_span

class TraceContextFilter(logging.Filter):
    def filter(self, record):
        span = get_current_span()
        ctx = span.get_span_context() if span else None

        record.trace_id = (
            format(ctx.trace_id, "032x") if ctx and ctx.trace_id else "-"
        )
        record.span_id = (
            format(ctx.span_id, "016x") if ctx and ctx.span_id else "-"
        )
        return True


def setup_logging(level=logging.INFO):
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s "
        "trace_id=%(trace_id)s span_id=%(span_id)s "
        "%(name)s: %(message)s"
    )

    handler.setFormatter(formatter)
    handler.addFilter(TraceContextFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)
