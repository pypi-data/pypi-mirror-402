import asyncio
from typing import List, Optional

from opentelemetry.trace import TracerProvider
from smolagents import CodeAgent

from quraite.adapters.base import BaseAdapter
from quraite.logger import get_logger
from quraite.schema.message import AgentMessage
from quraite.schema.response import AgentInvocationResponse
from quraite.tracing.constants import Framework
from quraite.tracing.trace import AgentSpan, AgentTrace

logger = get_logger(__name__)


class SmolagentsAdapter(BaseAdapter):
    """
    Smolagents adapter wrapper that converts any Smolagents CodeAgent
    to a standardized callable interface (ainvoke) with tracing support.

    This class wraps any CodeAgent and provides:
    - Asynchronous invocation via ainvoke()
    - OpenTelemetry tracing integration
    - Required tracing (returns AgentTrace containing spans)
    """

    def __init__(
        self,
        agent: CodeAgent,
        agent_name: str = "Smolagents Agent",
        tracer_provider: Optional[TracerProvider] = None,
    ):
        """
        Initialize with a pre-configured Smolagents CodeAgent

        Args:
            agent: A Smolagents CodeAgent instance
            agent_name: Name of the agent for trajectory metadata
            tracer_provider: TracerProvider for tracing (required)
        """
        logger.debug(
            "Initializing SmolagentsAdapter with agent_name=%s (tracing_required=True)",
            agent_name,
        )
        self._init_tracing(tracer_provider, required=True)

        self.agent = agent
        self.agent_name = agent_name
        logger.info("SmolagentsAdapter initialized successfully")

    def _prepare_input(self, input: List[AgentMessage]) -> str:
        """
        Prepare input for Smolagents CodeAgent from List[AgentMessage].

        Args:
            input: List[AgentMessage] containing user_message

        Returns:
            str: User message text
        """
        logger.debug("Preparing Smolagents input from %d messages", len(input))
        if not input or input[-1].role != "user":
            logger.error("Smolagents input missing user message")
            raise ValueError("No user message found in the input")

        last_user_message = input[-1]
        if not last_user_message.content:
            logger.error("Smolagents user message missing content")
            raise ValueError("User message has no content")

        text_content = None
        for content_item in last_user_message.content:
            if content_item.type == "text" and content_item.text:
                text_content = content_item.text
                break

        if not text_content:
            logger.error("Smolagents user message missing text content")
            raise ValueError("No text content found in user message")

        logger.debug("Prepared Smolagents input (text_length=%d)", len(text_content))
        return text_content

    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Optional[str] = None,
    ) -> AgentInvocationResponse:
        """
        Asynchronous invocation method - invokes the Smolagents CodeAgent with tracing

        Args:
            input: List[AgentMessage] containing user_message
            session_id: Optional conversation ID (for parity with other adapters)

        Returns:
            AgentTrace - trace with spans captured during invocation
        """
        _ = session_id  # Currently unused but kept for interface compatibility
        logger.info(
            "Smolagents ainvoke called (session_id=%s, input_messages=%d)",
            session_id,
            len(input),
        )
        agent_input = self._prepare_input(input)

        try:
            return await self._ainvoke_with_tracing(agent_input)
        except Exception as exc:
            logger.exception("Error invoking Smolagents agent")
            raise RuntimeError(f"Error invoking Smolagents agent: {exc}") from exc

    async def _ainvoke_with_tracing(self, agent_input: str) -> AgentInvocationResponse:
        """Execute ainvoke with tracing enabled."""
        with self.tracer.start_as_current_span("smolagents_invocation") as span:
            trace_id = span.get_span_context().trace_id
            logger.debug(
                "Starting Smolagents traced invocation (trace_id=%s)", trace_id
            )
            # Run the agent synchronously inside a thread to avoid blocking
            await asyncio.to_thread(self.agent.run, agent_input)

        trace_readable_spans = self.quraite_span_exporter.get_spans_by_trace_id(
            trace_id
        )

        if trace_readable_spans:
            logger.info(
                "Smolagents trace collected %d spans for trace_id=%s",
                len(trace_readable_spans),
                trace_id,
            )
            agent_trace = AgentTrace(
                spans=[
                    AgentSpan.from_readable_oi_span(span)
                    for span in trace_readable_spans
                ],
            )
        else:
            logger.warning("No spans captured for Smolagents trace_id=%s", trace_id)

        return AgentInvocationResponse(
            agent_trace=agent_trace,
            agent_trajectory=agent_trace.to_agent_trajectory(
                framework=Framework.SMOLAGENTS
            ),
        )
