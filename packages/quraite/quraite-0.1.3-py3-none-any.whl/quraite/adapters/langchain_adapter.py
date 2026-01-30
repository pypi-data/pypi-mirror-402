import json
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph
from opentelemetry.trace import TracerProvider

from quraite.adapters.base import BaseAdapter
from quraite.logger import get_logger
from quraite.schema.message import AgentMessage, AssistantMessage, MessageContentText
from quraite.schema.message import SystemMessage as QuraiteSystemMessage
from quraite.schema.message import ToolCall
from quraite.schema.message import ToolMessage as QuraiteToolMessage
from quraite.schema.message import UserMessage
from quraite.schema.response import AgentInvocationResponse
from quraite.tracing.constants import Framework
from quraite.tracing.trace import AgentSpan, AgentTrace

LangchainMessage = HumanMessage | SystemMessage | AIMessage | ToolMessage

logger = get_logger(__name__)


class LangchainAdapter(BaseAdapter):
    """
    LangChain adapter wrapper that converts any LangChain agent
    to a standardized callable interface (invoke) and converts the output to List[AgentMessage].

    This class wraps any LangChain CompiledGraph and provides:
    - Synchronous invocation via invoke()
    - Asynchronous invocation via ainvoke()
    - Automatic conversion to List[AgentMessage] format
    """

    def __init__(
        self,
        agent_graph: CompiledStateGraph,
        agent_name: str = "LangChain Agent",
        tracer_provider: Optional[TracerProvider] = None,
    ):
        """
        Initialize with a pre-configured LangChain agent

        Args:
            agent_graph: Any CompiledGraph from LangChain (must have invoke/ainvoke methods)
            agent_name: Name of the agent for trajectory metadata
        """
        logger.debug("Initializing LangchainAdapter with agent_name=%s", agent_name)
        self.agent_graph = agent_graph
        self.agent_name = agent_name
        self._init_tracing(tracer_provider, required=False)
        logger.info(
            "LangchainAdapter initialized successfully (tracing_enabled=%s)",
            bool(tracer_provider),
        )

    def _prepare_input(
        self, input: list[AgentMessage]
    ) -> dict[str, list[HumanMessage]]:
        """
        Prepare input for LangChain agent from List[Message].

        Args:
            input: List[AgentMessage] containing user_message

        Returns:
            Dictionary with 'messages' key containing the prepared UserMessage
        """
        logger.debug("Preparing input from %d messages", len(input))

        if not input or input[-1].role != "user":
            logger.error(
                "Invalid input: no user message found (input_length=%d)", len(input)
            )
            raise ValueError("No user message found in the input")

        last_user_message = input[-1]

        if not last_user_message.content:
            logger.error("User message has no content")
            raise ValueError("User message has no content")

        text_content = next(
            (
                content_item.text
                for content_item in last_user_message.content
                if content_item.type == "text" and content_item.text
            ),
            None,
        )

        if not text_content:
            logger.error("No text content found in user message")
            raise ValueError("No text content found in user message")

        logger.debug("Prepared input with text_content length=%d", len(text_content))
        return {"messages": [HumanMessage(content=text_content)]}

    def _convert_langchain_messages_to_quraite_messages(
        self,
        messages: list[LangchainMessage],
    ) -> list[AgentMessage]:
        logger.debug(
            "Converting %d langchain messages to quraite format", len(messages)
        )
        converted_messages: list[AgentMessage] = []

        for idx, msg in enumerate(messages):
            match msg:
                case SystemMessage():
                    logger.debug("Converting SystemMessage at index %d", idx)
                    converted_messages.append(
                        QuraiteSystemMessage(
                            content=[MessageContentText(type="text", text=msg.content)]
                        )
                    )

                case HumanMessage():
                    logger.debug("Converting HumanMessage at index %d", idx)
                    converted_messages.append(
                        UserMessage(
                            content=[MessageContentText(type="text", text=msg.content)]
                        )
                    )

                case AIMessage():
                    logger.debug(
                        "Converting AIMessage at index %d (has_tool_calls=%s)",
                        idx,
                        bool(msg.tool_calls),
                    )
                    text_content, tool_calls = self._extract_ai_message_content(msg)
                    converted_messages.append(
                        AssistantMessage(
                            content=text_content if text_content else None,
                            tool_calls=tool_calls if tool_calls else None,
                        )
                    )

                case ToolMessage():
                    logger.debug(
                        "Converting ToolMessage at index %d (tool_call_id=%s)",
                        idx,
                        msg.tool_call_id,
                    )
                    if not msg.content:
                        tool_message_content = ""
                    elif isinstance(msg.content, str):
                        tool_message_content = msg.content
                    else:
                        tool_message_content = json.dumps(msg.content)

                    converted_messages.append(
                        QuraiteToolMessage(
                            tool_call_id=msg.tool_call_id,
                            content=[
                                MessageContentText(
                                    type="text", text=tool_message_content
                                )
                            ],
                        )
                    )

        logger.info("Converted %d messages successfully", len(converted_messages))
        return converted_messages

    def _extract_ai_message_content(
        self, msg: AIMessage
    ) -> tuple[list[MessageContentText], list[ToolCall]]:
        text_content = []

        if msg.content:
            match msg.content:
                case str(text):
                    text_content.append(MessageContentText(type="text", text=text))
                case list():
                    text_content.extend(
                        MessageContentText(type="text", text=content.get("text"))
                        for content in msg.content
                        if isinstance(content, dict) and content.get("type") == "text"
                    )

        tool_calls = []
        if msg.tool_calls:
            logger.debug("Extracting %d tool calls from AIMessage", len(msg.tool_calls))
            tool_calls.extend(
                ToolCall(
                    id=tool_call.get("id"),  # type: ignore[union-attr]
                    name=tool_call.get("name"),  # type: ignore[union-attr]
                    arguments=tool_call.get("args"),  # type: ignore[union-attr]
                )
                for tool_call in msg.tool_calls
            )

        return text_content, tool_calls

    async def ainvoke(
        self,
        input: list[AgentMessage],
        session_id: str | None,
    ) -> AgentInvocationResponse:
        """
        Asynchronous invocation method - invokes the LangChain agent and converts the output to List[AgentMessage]

        Args:
            input: List[AgentMessage] containing user_message
            session_id: Optional conversation ID for maintaining context

        Returns:
            List[AgentMessage] or AgentTrace - converted messages from the agent's response or trace
        """
        logger.info(
            "ainvoke called (session_id=%s, input_messages=%d)", session_id, len(input)
        )

        try:
            agent_input = self._prepare_input(input)
            config = {"configurable": {"thread_id": session_id}} if session_id else {}

            if self.tracer_provider:
                logger.debug("Invoking with tracing enabled")
                return await self._ainvoke_with_tracing(agent_input, config)

            logger.debug("Invoking without tracing")
            return await self._ainvoke_without_tracing(agent_input, config)

        except ValueError:
            logger.exception("ValueError during ainvoke")
            raise
        except Exception:
            logger.exception("Unexpected error during ainvoke")
            raise

    async def _ainvoke_with_tracing(
        self,
        agent_input: dict[str, list[HumanMessage]],
        config: dict,
    ) -> AgentInvocationResponse:
        """Execute ainvoke with tracing enabled."""
        with self.tracer.start_as_current_span("langchain_invocation") as span:
            trace_id = span.get_span_context().trace_id
            logger.debug(
                "Starting LangChain traced invocation (trace_id=%s)",
                trace_id,
            )
            _ = await self.agent_graph.ainvoke(agent_input, config=config)

        trace_readable_spans = self.quraite_span_exporter.get_spans_by_trace_id(
            trace_id
        )

        if trace_readable_spans:
            logger.info("Retrieved %d spans from trace", len(trace_readable_spans))
            agent_trace = AgentTrace(
                spans=[
                    AgentSpan.from_readable_oi_span(span)
                    for span in trace_readable_spans
                ]
            )

            trajectory = agent_trace.to_agent_trajectory(framework=Framework.LANGCHAIN)
            logger.debug("Generated trajectory with %d messages", len(trajectory))

            return AgentInvocationResponse(
                agent_trace=agent_trace,
                agent_trajectory=trajectory,
            )

        logger.warning("No trace spans found for trace_id=%s", trace_id)
        return AgentInvocationResponse()

    async def _ainvoke_without_tracing(
        self,
        agent_input: dict[str, list[HumanMessage]],
        config: dict,
    ) -> AgentInvocationResponse:
        """Execute ainvoke without tracing."""
        logger.debug("Starting non-traced invocation")
        agent_messages = []

        try:
            async for event in self.agent_graph.astream(agent_input, config=config):
                logger.debug(
                    "Received stream event with %d values", len(event.values())
                )
                for result in event.values():
                    if messages := result.get("messages"):
                        logger.debug("Processing %d messages from event", len(messages))
                        agent_messages.extend(messages)

            logger.info(
                "Streaming complete, received %d total messages", len(agent_messages)
            )

            agent_trajectory = self._convert_langchain_messages_to_quraite_messages(
                agent_messages
            )

            return AgentInvocationResponse(
                agent_trajectory=agent_trajectory,
            )

        except ValueError:
            logger.exception("Error converting messages to List[AgentMessage]")
            return AgentInvocationResponse()
