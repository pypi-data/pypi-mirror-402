from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from opentelemetry.trace import Tracer, TracerProvider

from quraite.schema.message import AgentMessage, AssistantMessage, MessageContentText
from quraite.schema.response import AgentInvocationResponse
from quraite.tracing.constants import QURAITE_TRACER_NAME
from quraite.tracing.span_exporter import QuraiteInMemorySpanExporter
from quraite.tracing.span_processor import QuraiteSimpleSpanProcessor


class BaseAdapter(ABC):
    """
    Abstract base class for all adapter providers.

    Subclasses must implement the asynchronous adapter method,
    which take List[Message] and return agent Message outputs.

    Methods:
        ainvoke: Asynchronously invoke an agent call for the provided input.
    """

    tracer_provider: Optional[TracerProvider] = None
    tracer: Optional[Tracer] = None
    quraite_span_exporter: Optional[QuraiteInMemorySpanExporter] = None

    def _init_tracing(
        self,
        tracer_provider: Optional[TracerProvider],
        required: bool = False,
    ) -> None:
        """
        Initialize tracing components from a TracerProvider.

        Args:
            tracer_provider: TracerProvider for tracing
            span_exporter: SpanExporter for exporting spans
            required: If True, raises ValueError when tracer_provider is None
        """
        if tracer_provider is None:
            if required:
                raise ValueError(
                    "tracer_provider is required. "
                    "Please provide a TracerProvider instance."
                )
            return

        self.tracer_provider = tracer_provider
        self.tracer = tracer_provider.get_tracer(QURAITE_TRACER_NAME)

        # Find Quraite span exporter
        quraite_span_exporter = next(
            (
                processor.span_exporter
                for processor in tracer_provider._active_span_processor._span_processors
                if isinstance(processor, QuraiteSimpleSpanProcessor)
            ),
            None,
        )

        if quraite_span_exporter is None:
            raise ValueError(
                "Quraite span exporter not found. "
                "Please ensure QuraiteSimpleSpanProcessor is used in the tracer provider."
            )

        self.quraite_span_exporter = quraite_span_exporter

    @abstractmethod
    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Union[str, None],
    ) -> AgentInvocationResponse:
        """
        Asynchronously invoke the agent with the given input.

        Args:
            input (List[AgentMessage]): List of AgentMessage objects.
            session_id (str or None): ID for conversation thread/context.

        Returns:
            AgentInvocationResponse: Response containing agent trace, trajectory, and final response.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError("Not implemented")


class DummyAdapter(BaseAdapter):
    """
    A dummy implementation of BaseAdapter, used mainly for testing and scaffolding.
    Always returns a fixed dummy response.

    Methods:
        ainvoke: Returns a static assistant message asynchronously.
    """

    async def ainvoke(
        self,
        input: Any,
        session_id: Union[str, None],
    ) -> AgentInvocationResponse:
        """
        Asynchronously returns a dummy assistant response.

        Args:
            input: Ignored.
            session_id: Ignored.

        Returns:
            AgentInvocationResponse: Response containing agent trace, trajectory, and final response.
        """

        return AgentInvocationResponse(
            agent_trajectory=[
                AssistantMessage(
                    content=[MessageContentText(text="Dummy response")],
                )
            ]
        )
