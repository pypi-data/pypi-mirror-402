import json
from typing import Dict, List, Optional, Union

from agents import (
    Agent,
    MessageOutputItem,
    ReasoningItem,
    RunItem,
    Runner,
    SQLiteSession,
    ToolCallItem,
    ToolCallOutputItem,
    TResponseInputItem,
)
from agents.memory import Session
from opentelemetry.trace import TracerProvider

from quraite.adapters.base import BaseAdapter
from quraite.logger import get_logger
from quraite.schema.message import (
    AgentMessage,
    AssistantMessage,
    MessageContentReasoning,
    MessageContentText,
    ToolCall,
    ToolMessage,
)
from quraite.schema.response import AgentInvocationResponse
from quraite.tracing.constants import Framework
from quraite.tracing.trace import AgentSpan, AgentTrace

logger = get_logger(__name__)


class OpenaiAgentsAdapter(BaseAdapter):
    def __init__(
        self,
        agent: Agent,
        agent_name: str = "OpenAI Agents",
        tracer_provider: Optional[TracerProvider] = None,
    ):
        self.agent = agent
        self.sessions: Dict[str, Session] = {}
        self._init_tracing(tracer_provider, required=False)
        self.agent_name = agent_name
        logger.info(
            "OpenaiAgentsAdapter initialized (agent_name=%s, tracing_enabled=%s)",
            agent_name,
            bool(tracer_provider),
        )

    def _convert_run_items_to_messages(
        self, run_items: List[RunItem]
    ) -> List[AgentMessage]:
        logger.debug("Converting %d OpenAI run items to messages", len(run_items))
        messages: List[AgentMessage] = []
        text_content: List[MessageContentText] = []
        reasoning_content: List[MessageContentReasoning] = []
        tool_calls: List[ToolCall] = []

        def flush_assistant_message():
            nonlocal text_content, reasoning_content, tool_calls
            if text_content or reasoning_content or tool_calls:
                content = []
                if text_content:
                    content.extend(text_content)
                if reasoning_content:
                    content.extend(reasoning_content)
                messages.append(
                    AssistantMessage(
                        content=content if content else None,
                        tool_calls=tool_calls if tool_calls else None,
                    )
                )
            text_content = []
            reasoning_content = []
            tool_calls = []

        for item in run_items:
            if item.type in [
                "handoff_call_item",
                "handoff_output_item",
                "mcp_list_tools_item",
                "mcp_approval_request_item",
                "mcp_approval_response_item",
            ]:
                continue

            if isinstance(item, MessageOutputItem):
                text_parts = []
                for content_item in item.raw_item.content:
                    if hasattr(content_item, "text"):
                        text_parts.append(content_item.text)
                if text_parts:
                    text_content.append(
                        MessageContentText(type="text", text="".join(text_parts))
                    )

            elif isinstance(item, ReasoningItem):
                if item.raw_item.summary:
                    summary = ""
                    for summary_item in item.raw_item.summary:
                        summary += summary_item.text
                        summary += "\n"
                    reasoning_content.append(
                        MessageContentReasoning(type="reasoning", reasoning=summary)
                    )

            elif isinstance(item, ToolCallItem):
                raw = item.raw_item
                arguments = None
                if hasattr(raw, "arguments"):
                    try:
                        arguments = (
                            json.loads(raw.arguments)
                            if isinstance(raw.arguments, str)
                            else raw.arguments
                        )
                    except:
                        arguments = {"raw": str(raw.arguments)}
                tool_calls.append(
                    ToolCall(
                        id=getattr(raw, "call_id", ""),
                        name=getattr(raw, "name", ""),
                        arguments=arguments or {},
                    )
                )

            elif isinstance(item, ToolCallOutputItem):
                flush_assistant_message()
                tool_result = json.dumps({"output": item.output})
                messages.append(
                    ToolMessage(
                        tool_call_id=item.raw_item.get("call_id", ""),
                        content=[MessageContentText(type="text", text=tool_result)],
                    )
                )
                continue

        flush_assistant_message()
        logger.info("Converted OpenAI agent run into %d messages", len(messages))
        return messages

    def _prepare_input(self, input: List[AgentMessage]) -> str:
        logger.debug("Preparing OpenAI input from %d messages", len(input))
        if not input or input[-1].role != "user":
            logger.error("OpenAI input missing user message")
            raise ValueError("No user message found in the input")

        last_user_message = input[-1]
        if not last_user_message.content:
            logger.error("OpenAI user message missing content")
            raise ValueError("User message has no content")

        text_content = None
        for content_item in last_user_message.content:
            if content_item.type == "text" and content_item.text:
                text_content = content_item.text
                break

        if not text_content:
            logger.error("OpenAI user message missing text content")
            raise ValueError("No text content found in user message")

        logger.debug("Prepared OpenAI input (text_length=%d)", len(text_content))
        return text_content

    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Union[str, None] = None,
    ) -> AgentInvocationResponse:
        """Asynchronous invocation method - invokes the OpenAI Agents agent and converts to List[AgentMessage]."""
        try:
            logger.info(
                "OpenAI ainvoke called (session_id=%s, input_messages=%d)",
                session_id,
                len(input),
            )
            agent_input: Union[str, List[TResponseInputItem]] = self._prepare_input(
                input
            )

            if session_id not in self.sessions:
                self.sessions[session_id] = SQLiteSession(session_id=session_id)
            session = self.sessions[session_id]

            if self.tracer_provider:
                return await self._ainvoke_with_tracing(agent_input, session)

            return await self._ainvoke_without_tracing(agent_input, session)
        except Exception as exc:
            logger.exception("Error invoking OpenAI agent")
            raise Exception(f"Error invoking Openai agent: {exc}") from exc

    async def _ainvoke_with_tracing(
        self,
        agent_input: Union[str, List[TResponseInputItem]],
        session: Session,
    ) -> AgentInvocationResponse:
        """Execute ainvoke with tracing enabled."""
        with self.tracer.start_as_current_span("openai_invocation") as span:
            trace_id = span.get_span_context().trace_id
            logger.debug(
                "Starting OpenAI traced invocation (trace_id=%s session_id=%s)",
                trace_id,
                session.session_id if session else None,
            )
            await Runner.run(
                self.agent,
                input=agent_input,
                session=session,
            )

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
                "OpenAI trace collected %d spans for trace_id=%s",
                len(trace_readable_spans),
                trace_id,
            )
        else:
            logger.warning(
                "No spans exported for OpenAI trace_id=%s",
                trace_id,
            )

        return AgentInvocationResponse(
            agent_trace=agent_trace,
            agent_trajectory=agent_trace.to_agent_trajectory(
                framework=Framework.OPENAI_AGENTS
            ),
        )

    async def _ainvoke_without_tracing(
        self,
        agent_input: Union[str, List[TResponseInputItem]],
        session: Session,
    ) -> AgentInvocationResponse:
        """Execute ainvoke without tracing."""
        result = await Runner.run(
            self.agent,
            input=agent_input,
            session=session,
        )

        try:
            agent_trajectory = self._convert_run_items_to_messages(result.new_items)
            logger.info(
                "OpenAI agent produced %d trajectory messages (no tracing)",
                len(agent_trajectory),
            )
            return AgentInvocationResponse(
                agent_trajectory=agent_trajectory,
            )
        except Exception as exc:
            logger.exception("Error converting OpenAI run items to messages")
            raise Exception(f"Error converting run items to messages: {exc}") from exc
