import typing

from opentelemetry.context import (
    _SUPPRESS_INSTRUMENTATION_KEY,
    Context,
    attach,
    detach,
    set_value,
)
from opentelemetry.sdk.trace.export import ReadableSpan, SpanExporter, SpanProcessor
from opentelemetry.trace import Span, logger

from quraite.tracing.span_exporter import QuraiteInMemorySpanExporter


class QuraiteSimpleSpanProcessor(SpanProcessor):
    """Simple SpanProcessor implementation.

    SimpleSpanProcessor is an implementation of `SpanProcessor` that
    passes ended spans directly to the configured `SpanExporter`.
    """

    def __init__(self, span_exporter: SpanExporter):
        self.span_exporter: QuraiteInMemorySpanExporter = span_exporter

    def on_start(
        self, span: Span, parent_context: typing.Optional[Context] = None
    ) -> None:
        pass

    def on_end(self, span: ReadableSpan) -> None:
        if not span.context.trace_flags.sampled:
            return
        token = attach(set_value(_SUPPRESS_INSTRUMENTATION_KEY, True))
        try:
            self.span_exporter.export((span,))
        # pylint: disable=broad-exception-caught
        except Exception:
            logger.exception("Exception while exporting Span.")
        detach(token)

    def shutdown(self) -> None:
        self.span_exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        # pylint: disable=unused-argument
        return True
