from typing import Any, List, Union

from opentelemetry.trace import TracerProvider
from pydantic_ai import Agent
from pydantic_ai.messages import (
    BuiltinToolCallPart,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from quraite.adapters.base import BaseAdapter
from quraite.logger import get_logger
from quraite.schema.message import (
    AgentMessage,
    AssistantMessage,
    MessageContentText,
    ToolCall,
    ToolMessage,
)
from quraite.schema.response import AgentInvocationResponse
from quraite.tracing.constants import Framework
from quraite.tracing.trace import AgentSpan, AgentTrace

logger = get_logger(__name__)


class PydanticAIAdapter(BaseAdapter):
    """
    Pydantic AI adapter wrapper that converts any Pydantic AI agent
    to a standardized callable interface (invoke) and converts the output to List[AgentMessage].

    This class wraps any Pydantic AI Agent and provides:
    - Synchronous invocation via invoke()
    - Asynchronous invocation via ainvoke()
    - Automatic conversion to List[AgentMessage] format
    - Access to message history and traces
    """

    def __init__(
        self,
        agent: Agent,
        agent_name: str = "Pydantic AI Agent",
        tracer_provider: TracerProvider | None = None,
    ):
        """
        Initialize with a pre-configured Pydantic AI agent

        Args:
            agent: A Pydantic AI Agent instance
            agent_name: Name of the agent for trajectory metadata
        """
        self.agent = agent
        self.agent_name = agent_name
        # Store session state for conversation context
        self._sessions: dict[str, Any] = {}
        self._init_tracing(tracer_provider, required=False)
        logger.info(
            "PydanticAIAdapter initialized (agent_name=%s, tracing_enabled=%s)",
            agent_name,
            bool(tracer_provider),
        )

    def _convert_pydantic_ai_messages_to_messages(
        self, messages: List[Any]
    ) -> List[AgentMessage]:
        """
        Convert Pydantic AI ModelMessage objects (with parts) to SDK Message format.

        Args:
            messages: List of Pydantic AI ModelMessage objects

        Returns:
            List[AgentMessage]: Converted messages in SDK format
        """
        converted_messages: List[AgentMessage] = []

        for msg in messages:
            if not hasattr(msg, "parts"):
                continue

            content: List[MessageContentText] = []
            tool_calls_list: List[ToolCall] = []

            for part in msg.parts:
                if isinstance(part, SystemPromptPart) or isinstance(
                    part, UserPromptPart
                ):
                    continue

                elif isinstance(part, TextPart):
                    if part.content:
                        content.append(
                            MessageContentText(type="text", text=part.content)
                        )
                elif isinstance(part, ToolCallPart) or isinstance(
                    part, BuiltinToolCallPart
                ):
                    tool_call_id = part.tool_call_id
                    tool_name = part.tool_name
                    args = part.args

                    tool_calls_list.append(
                        ToolCall(
                            id=tool_call_id,
                            name=tool_name,
                            arguments=args if isinstance(args, dict) else {},
                        )
                    )

                elif isinstance(part, ToolReturnPart):
                    if content or tool_calls_list:
                        converted_messages.append(
                            AssistantMessage(
                                content=content if content else None,
                                tool_calls=tool_calls_list if tool_calls_list else None,
                            )
                        )
                        content = []
                        tool_calls_list = []

                    tool_call_id = part.tool_call_id

                    converted_messages.append(
                        ToolMessage(
                            tool_name=part.tool_name,
                            tool_call_id=tool_call_id,
                            content=[
                                MessageContentText(type="text", text=str(part.content))
                            ],
                        )
                    )

            if content or tool_calls_list:
                converted_messages.append(
                    AssistantMessage(
                        content=content if content else None,
                        tool_calls=tool_calls_list if tool_calls_list else None,
                    )
                )

        logger.info(
            "Converted %d Pydantic AI messages to agent messages",
            len(converted_messages),
        )
        return converted_messages

    def _prepare_input(self, input: List[AgentMessage]) -> str:
        """
        Prepare input for Pydantic AI agent from List[AgentMessage].

        Args:
            input: List[AgentMessage] containing user_message

        Returns:
            str: User message text
        """
        logger.debug("Preparing Pydantic AI input from %d messages", len(input))
        if not input or input[-1].role != "user":
            logger.error("Pydantic AI input missing user message")
            raise ValueError("No user message found in the input")

        last_user_message = input[-1]
        if not last_user_message.content:
            logger.error("Pydantic AI user message missing content")
            raise ValueError("User message has no content")

        text_content = None
        for content_item in last_user_message.content:
            if content_item.type == "text" and content_item.text:
                text_content = content_item.text
                break

        if not text_content:
            logger.error("Pydantic AI user message missing text content")
            raise ValueError("No text content found in user message")

        logger.debug("Prepared Pydantic AI input (text_length=%d)", len(text_content))
        return text_content

    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Union[str, None],
    ) -> AgentInvocationResponse:
        """
        Asynchronous invocation method - invokes the Pydantic AI agent and converts the output to List[AgentMessage]

        Args:
            input: List[AgentMessage] containing user_message
            session_id: Optional conversation ID for maintaining context

        Returns:
            AgentInvocationResponse - response containing agent trace, trajectory, and final response.
        """
        logger.info(
            "Pydantic AI ainvoke called (session_id=%s, input_messages=%d)",
            session_id,
            len(input),
        )
        agent_input = self._prepare_input(input)
        session_id = session_id or "default"

        try:
            # Get message history for this session (for multi-turn conversations)
            message_history = self._sessions.get(session_id, None)

            # Run with or without tracing depending on configuration
            if self.tracer_provider:
                return await self._ainvoke_with_tracing(
                    agent_input, session_id, message_history
                )

            return await self._ainvoke_without_tracing(
                agent_input, session_id, message_history
            )

        except Exception as e:
            logger.exception("Error invoking Pydantic AI agent")
            raise RuntimeError(f"Error invoking Pydantic AI agent: {e}") from e

    async def _ainvoke_with_tracing(
        self,
        agent_input: str,
        session_id: str,
        message_history: Any | None,
    ) -> AgentInvocationResponse:
        """Execute ainvoke with tracing enabled."""
        with self.tracer.start_as_current_span("pydantic_invocation") as span:
            trace_id = span.get_span_context().trace_id
            logger.debug(
                "Starting Pydantic AI traced invocation (trace_id=%s session_id=%s)",
                trace_id,
                session_id,
            )
            # Run the agent asynchronously with message history for context
            if message_history:
                result = await self.agent.run(
                    agent_input,
                    message_history=message_history,
                )
            else:
                result = await self.agent.run(agent_input)

        # Store the complete updated message history for this session
        self._sessions[session_id] = result.all_messages()

        trace_readable_spans = self.quraite_span_exporter.get_spans_by_trace_id(
            trace_id
        )

        if trace_readable_spans:
            agent_trace = AgentTrace(
                spans=[
                    AgentSpan.from_readable_oi_span(span)
                    for span in trace_readable_spans
                ]
            )
            logger.info(
                "Pydantic AI trace collected %d spans for trace_id=%s",
                len(trace_readable_spans),
                trace_id,
            )
        else:
            logger.warning("No spans exported for Pydantic AI trace_id=%s", trace_id)

        return AgentInvocationResponse(
            agent_trace=agent_trace,
            agent_trajectory=agent_trace.to_agent_trajectory(
                framework=Framework.PYDANTIC_AI
            ),
        )

    async def _ainvoke_without_tracing(
        self,
        agent_input: str,
        session_id: str,
        message_history: Any | None,
    ) -> AgentInvocationResponse:
        """Execute ainvoke without tracing."""
        # Run the agent asynchronously with message history for context
        if message_history:
            result = await self.agent.run(
                agent_input,
                message_history=message_history,
            )
        else:
            result = await self.agent.run(agent_input)

        # Store the complete updated message history for this session
        self._sessions[session_id] = result.all_messages()

        # Convert only the NEW messages to SDK Message format
        agent_trajectory = self._convert_pydantic_ai_messages_to_messages(
            result.new_messages()
        )

        logger.info(
            "Pydantic AI produced %d trajectory messages without tracing",
            len(agent_trajectory),
        )

        return AgentInvocationResponse(
            agent_trajectory=agent_trajectory,
        )
