import uuid
from typing import List, Union

from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.errors.already_exists_error import AlreadyExistsError
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService, InMemorySessionService
from google.genai import types
from opentelemetry.trace import TracerProvider

from quraite.adapters.base import BaseAdapter
from quraite.logger import get_logger
from quraite.schema.message import AgentMessage
from quraite.schema.response import AgentInvocationResponse
from quraite.tracing.constants import Framework
from quraite.tracing.trace import AgentSpan, AgentTrace

logger = get_logger(__name__)


class GoogleADKAdapter(BaseAdapter):
    """
    Google ADK adapter wrapper that converts any Google ADK agent
    to a standardized callable interface (ainvoke) with tracing support.

    This class wraps any Google ADK Agent and provides:
    - Asynchronous invocation via ainvoke()
    - OpenTelemetry tracing integration
    - Session management for multi-turn conversations
    """

    def __init__(
        self,
        agent: Agent,
        agent_name: str = "Google ADK Agent",
        tracer_provider: TracerProvider = None,
        app_name: str = "google_adk_agent",
        user_id: str = str(uuid.uuid4()),
        session_service: BaseSessionService = InMemorySessionService(),
    ):
        """
        Initialize with a pre-configured Google ADK agent

        Args:
            agent: A Google ADK Agent instance
            app_name: Application name for ADK runner
            agent_name: Name of the agent for trajectory metadata
            tracer_provider: TracerProvider for tracing (required)
        """
        logger.debug(
            "Initializing GoogleADKAdapter (agent_name=%s, app_name=%s)",
            agent_name,
            app_name,
        )
        self._init_tracing(tracer_provider, required=True)

        self.agent: Agent = agent
        self.app_name = app_name
        self.agent_name = agent_name
        self.session_service = session_service
        self.user_id = user_id
        self.app = App(
            name=app_name,
            root_agent=agent,
        )
        self.runner = Runner(
            app=self.app,
            session_service=session_service,
        )
        logger.info("GoogleADKAdapter initialized successfully")

    def _prepare_input(self, input: List[AgentMessage]) -> str:
        """
        Prepare input for Google ADK agent from List[Message].

        Args:
            input: List[Message] containing user_message

        Returns:
            str: User message text
        """
        logger.debug("Preparing Google ADK input from %d messages", len(input))
        if not input or input[-1].role != "user":
            logger.error("Google ADK input missing user message")
            raise ValueError("No user message found in the input")

        last_user_message = input[-1]
        # Check if content list is not empty and has text
        if not last_user_message.content:
            logger.error("Google ADK user message missing content")
            raise ValueError("User message has no content")

        # Find the first text content item
        text_content = None
        for content_item in last_user_message.content:
            if content_item.type == "text" and content_item.text:
                text_content = content_item.text
                break

        if not text_content:
            logger.error("Google ADK user message missing text content")
            raise ValueError("No text content found in user message")

        logger.debug("Prepared Google ADK input (text_length=%d)", len(text_content))
        return text_content

    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Union[str, None] = None,
    ) -> AgentInvocationResponse:
        """
        Asynchronous invocation method - invokes the Google ADK agent with tracing

        Args:
            input: List[AgentMessage] containing user_message
            session_id: Optional conversation ID for maintaining context

        Returns:
            AgentInvocationResponse - response containing agent trace, trajectory, and final response.
        """
        logger.info(
            "Google ADK ainvoke called (session_id=%s, input_messages=%d)",
            session_id,
            len(input),
        )
        agent_input = self._prepare_input(input)
        session_id = session_id or str(uuid.uuid4())

        try:
            return await self._ainvoke_with_tracing(agent_input, session_id)

        except Exception as e:
            logger.exception("Error invoking Google ADK agent")
            raise RuntimeError(f"Error invoking Google ADK agent: {e}") from e

    async def _ainvoke_with_tracing(
        self,
        agent_input: str,
        session_id: str,
    ) -> AgentInvocationResponse:
        """Execute ainvoke with tracing enabled."""
        logger.debug(
            "Starting Google ADK traced invocation (session_id=%s)",
            session_id,
        )

        with self.tracer.start_as_current_span("google_adk_invocation") as span:
            trace_id = span.get_span_context().trace_id
            logger.debug(
                "Starting Google ADK traced invocation (trace_id=%s, session_id=%s)",
                trace_id,
                session_id,
            )
            # Create session if it doesn't exist
            try:
                await self.session_service.create_session(
                    app_name=self.app_name,
                    user_id=self.user_id,
                    session_id=session_id,
                )
            except AlreadyExistsError:
                logger.info("Session already exists: %s", session_id)
            except Exception as e:
                logger.exception("Error creating Google ADK session")
                raise RuntimeError(f"Error creating session: {e}") from e

            # Create content for ADK
            content = types.Content(
                role="user",
                parts=[types.Part(text=agent_input)],
            )

            # Run async and consume events
            events = self.runner.run_async(
                new_message=content,
                user_id=self.user_id,
                session_id=session_id,
            )

            # Consume all events (tracing captures everything)
            async for event in events:
                pass  # Just consume events, tracing handles capture

        # Get trace spans
        trace_readable_spans = self.quraite_span_exporter.get_spans_by_trace_id(
            trace_id
        )

        if trace_readable_spans:
            agent_trace = AgentTrace(
                spans=[
                    AgentSpan.from_readable_oi_span(span)
                    for span in trace_readable_spans
                ],
            )
            logger.info(
                "Google ADK trace collected %d spans for trace_id=%s",
                len(trace_readable_spans),
                trace_id,
            )
        else:
            logger.warning("No spans exported for Google ADK trace_id=%s", trace_id)

        return AgentInvocationResponse(
            agent_trace=agent_trace,
            agent_trajectory=agent_trace.to_agent_trajectory(
                framework=Framework.GOOGLE_ADK
            ),
        )
