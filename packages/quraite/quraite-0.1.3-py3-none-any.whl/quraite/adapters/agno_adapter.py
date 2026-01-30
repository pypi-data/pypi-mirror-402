from typing import List, Union

from agno.agent import Agent
from agno.team import Team
from opentelemetry.trace import TracerProvider

from quraite.adapters.base import BaseAdapter
from quraite.logger import get_logger
from quraite.schema.message import AgentMessage
from quraite.schema.response import AgentInvocationResponse
from quraite.tracing.constants import Framework
from quraite.tracing.trace import AgentSpan, AgentTrace

logger = get_logger(__name__)


class AgnoAdapter(BaseAdapter):
    """
    Agno adapter wrapper that converts any Agno agent or team
    to a standardized callable interface (invoke) and converts the output to List[AgentMessage].

    This class wraps any Agno Agent or Team and provides:
    - Asynchronous invocation via ainvoke()
    - Automatic conversion to List[AgentMessage] format
    - Access to message history and traces
    - Support for both single agents and multi-agent teams
    """

    def __init__(
        self,
        agent: Union[Agent, Team],
        agent_name: str = "Agno Agent",
        tracer_provider: TracerProvider = None,
    ):
        """
        Initialize with a pre-configured Agno agent or team

        Args:
            agent: An Agno Agent or Team instance
            agent_name: Name of the agent for trajectory metadata
            tracer_provider: TracerProvider for tracing (required)
        """
        logger.debug("Initializing AgnoAdapter with agent_name=%s", agent_name)
        self._init_tracing(tracer_provider, required=True)

        self.agent: Union[Agent, Team] = agent
        self.agent_name = agent_name
        logger.info(
            "AgnoAdapter initialized successfully (tracing_enabled=%s)",
            bool(tracer_provider),
        )

    def _prepare_input(self, input: List[AgentMessage]) -> str:
        """
        Prepare input for Agno agent from List[AgentMessage].

        Args:
            input: List[AgentMessage] containing user_message

        Returns:
            str: User message text
        """
        logger.debug("Preparing input from %d messages", len(input))
        if not input or input[-1].role != "user":
            logger.error("Invalid input: no user message found")
            raise ValueError("No user message found in the input")

        last_user_message = input[-1]
        if not last_user_message.content:
            logger.error("User message has no content")
            raise ValueError("User message has no content")

        text_content = None
        for content_item in last_user_message.content:
            if content_item.type == "text" and content_item.text:
                text_content = content_item.text
                break

        if not text_content:
            logger.error("No text content found in user message")
            raise ValueError("No text content found in user message")

        logger.debug("Prepared input with text_content length=%d", len(text_content))
        return text_content

    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Union[str, None] = None,
    ) -> AgentInvocationResponse:
        """
        Asynchronous invocation method - invokes the Agno agent/team with tracing

        Args:
            input: List[AgentMessage] containing user_message
            session_id: Optional conversation ID for maintaining context

        Returns:
            AgentInvocationResponse - response containing agent trace, trajectory, and final response.
        """
        logger.info(
            "ainvoke called (session_id=%s, input_messages=%d)", session_id, len(input)
        )
        agent_input = self._prepare_input(input)
        session_id = session_id or "default"

        try:
            logger.debug("Invoking Agno agent with tracing (session_id=%s)", session_id)
            return await self._ainvoke_with_tracing(agent_input, session_id)

        except ValueError:
            logger.exception("Invalid input during ainvoke")
            raise
        except Exception as e:
            logger.exception("Unexpected error invoking Agno agent")
            raise RuntimeError(f"Error invoking Agno agent: {e}") from e

    async def _ainvoke_with_tracing(
        self,
        agent_input: str,
        session_id: str,
    ) -> AgentInvocationResponse:
        """Execute ainvoke with tracing enabled."""
        with self.tracer.start_as_current_span("agno_invocation") as span:
            trace_id = span.get_span_context().trace_id
            logger.debug(
                "Starting traced invocation (session_id=%s) with trace_id=%s",
                session_id,
                trace_id,
            )
            # Run the agent/team
            await self.agent.arun(agent_input, session_id=session_id)

        # Get trace spans
        trace_readable_spans = self.quraite_span_exporter.get_spans_by_trace_id(
            trace_id
        )

        if trace_readable_spans:
            logger.info(
                "Retrieved %d spans for trace_id=%s",
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
            logger.warning("No spans found for trace_id=%s", trace_id)

        return AgentInvocationResponse(
            agent_trace=agent_trace,
            agent_trajectory=agent_trace.to_agent_trajectory(framework=Framework.AGNO),
        )
