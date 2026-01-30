# mypy: disable-error-code="arg-type,attr-defined"
from __future__ import annotations

import json
from functools import cached_property
from typing import Any, List, Optional

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace import Span as OTelSpan
from pydantic import BaseModel, ConfigDict, Field

from quraite.logger import get_logger
from quraite.schema.message import AssistantMessage, AssistantMessageMetadata
from quraite.schema.message import CostInfo as MessageCostInfo
from quraite.schema.message import LatencyInfo as MessageLatencyInfo
from quraite.schema.message import MessageContentText
from quraite.schema.message import ModelInfo as MessageModelInfo
from quraite.schema.message import SystemMessage
from quraite.schema.message import TokenInfo as MessageTokenInfo
from quraite.schema.message import ToolCall, ToolMessage, ToolMessageMetadata
from quraite.tracing.constants import Framework
from quraite.tracing.types import Event, Link, Resource, SpanContext, SpanKind, Status
from quraite.tracing.utils import unflatten_messages

logger = get_logger(__name__)


class TokenInfo(BaseModel):
    """Token Count information."""

    input_tokens: int
    """Number of input tokens."""

    output_tokens: int
    """Number of output tokens."""

    @property
    def total_tokens(self) -> int:
        """Total number of tokens."""
        return self.input_tokens + self.output_tokens

    model_config = ConfigDict(extra="forbid")


class CostInfo(BaseModel):
    """Cost information."""

    input_cost: float
    "Cost associated to the input tokens."

    output_cost: float
    """Cost associated to the output tokens."""

    @property
    def total_cost(self) -> float:
        """Total cost."""
        return self.input_cost + self.output_cost

    model_config = ConfigDict(extra="forbid")


class AgentSpan(BaseModel):
    """A span that can be exported to JSON or printed to the console."""

    name: str
    kind: SpanKind
    parent: SpanContext | None = None
    start_time: int | None = None
    end_time: int | None = None
    status: Status
    context: SpanContext
    attributes: dict[str, Any]
    links: list[Link]
    events: list[Event]
    resource: Resource

    # TODO: Revisit this. It is supposed to be False.
    # If it is False, SpanContext causes it to fail.
    model_config = ConfigDict(arbitrary_types_allowed=False)

    @classmethod
    def from_otel(cls, otel_span: OTelSpan) -> AgentSpan:
        """Create an AgentSpan from an OTEL Span."""
        return cls(
            name=otel_span.name,
            kind=SpanKind.from_otel(otel_span.kind),
            parent=SpanContext.from_otel(otel_span.parent),
            start_time=otel_span.start_time,
            end_time=otel_span.end_time,
            status=Status.from_otel(otel_span.status),
            context=SpanContext.from_otel(otel_span.context),
            attributes=dict(otel_span.attributes) if otel_span.attributes else {},
            links=[Link.from_otel(link) for link in otel_span.links],
            events=[Event.from_otel(event) for event in otel_span.events],
            resource=Resource.from_otel(otel_span.resource),
        )

    @classmethod
    def from_readable_oi_span(cls, readable_span: ReadableSpan) -> AgentSpan:
        """Create an AgentSpan from a ReadableSpan."""
        return cls(
            name=readable_span.name,
            kind=SpanKind.from_otel(readable_span.kind),
            parent=SpanContext.from_otel(readable_span.parent),
            start_time=readable_span.start_time,
            end_time=readable_span.end_time,
            status=Status.from_otel(readable_span.status),
            context=SpanContext.from_otel(readable_span.context),
            attributes=(
                dict(readable_span.attributes) if readable_span.attributes else {}
            ),
            links=[Link.from_otel(link) for link in readable_span.links],
            events=[Event.from_otel(event) for event in readable_span.events],
            resource=Resource.from_otel(readable_span.resource),
        )

    def to_readable_span(self) -> ReadableSpan:
        """Create an ReadableSpan from the AgentSpan."""
        return ReadableSpan(
            name=self.name,
            kind=self.kind,
            parent=self.parent,
            start_time=self.start_time,
            end_time=self.end_time,
            status=self.status,
            context=self.context,
            attributes=self.attributes,
            links=self.links,
            events=self.events,
            resource=self.resource,
        )

    def is_agent_invocation(self) -> bool:
        """Check whether this span is an agent invocation (the very first span)."""
        return self.get_oi_span_kind() == OpenInferenceSpanKindValues.AGENT

    def is_llm_call(self) -> bool:
        """Check whether this span is a call to an LLM."""
        return self.get_oi_span_kind() == OpenInferenceSpanKindValues.LLM

    def is_tool_execution(self) -> bool:
        """Check whether this span is an execution of a tool."""
        return self.get_oi_span_kind() == OpenInferenceSpanKindValues.TOOL

    def get_oi_span_kind(self) -> OpenInferenceSpanKindValues:
        """Get the OpenInference span kind from the span."""

        return OpenInferenceSpanKindValues(
            self.attributes.get(
                SpanAttributes.OPENINFERENCE_SPAN_KIND,
                OpenInferenceSpanKindValues.UNKNOWN,
            )
        )

    def to_llm_messages(self) -> List[dict[str, Any]]:
        """
        Convert LLM span to output messages.

        Note: Removes function_call_name and function_call_arguments_json from messages.

        Returns:
            List of output messages from this LLM span
        """
        if not self.is_llm_call():
            return []

        # Extract output messages
        unflattened = unflatten_messages(self.attributes)
        output_msgs = unflattened.get("llm.output_messages", [])

        # Remove function_call_name and function_call_arguments_json from messages
        cleaned_messages = []
        for msg in output_msgs:
            if isinstance(msg, dict):
                cleaned_msg = {
                    k: v
                    for k, v in msg.items()
                    if k not in ("function_call_name", "function_call_arguments_json")
                }
                cleaned_messages.append(cleaned_msg)
            else:
                cleaned_messages.append(msg)

        return cleaned_messages

    def to_tool_message(
        self, framework: Framework = Framework.LANGCHAIN
    ) -> dict[str, Any] | None:
        """
        Convert tool execution span to a tool message.

        Args:
            framework: The agent framework to use for extraction

        Returns:
            Tool message dict or None if not a tool span or extraction fails
        """
        if not self.is_tool_execution():
            return None

        from .tool_extractors import get_tool_extractor

        # Convert AgentSpan to dict format for tool extractor
        span_dict = {
            "attributes": self.attributes,
            "context": {"span_id": self.context.span_id},
            "parent_id": (
                str(self.parent.span_id)
                if self.parent and self.parent.span_id
                else None
            ),
            "start_time": self.start_time,
        }

        # Extract tool info using framework-specific extractor
        tool_extractor = get_tool_extractor(framework)
        tool_info = tool_extractor(span_dict)

        if tool_info:
            return tool_info.to_dict()

        return None


class AgentTrace(BaseModel):
    """A trace that can be exported to JSON or printed to the console."""

    spans: list[AgentSpan] = Field(default_factory=list)
    """A list of [`AgentSpan`][any_agent.tracing.agent_trace.AgentSpan] that form the trace.
    """

    final_output: str | AssistantMessage | None = Field(default=None)
    """Contains the final output message returned by the agent.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _invalidate_tokens_and_cost_cache(self) -> None:
        """Clear the cached tokens_and_cost property if it exists."""
        if "tokens" in self.__dict__:
            del self.tokens
        if "cost" in self.__dict__:
            del self.cost

    def add_span(self, span: AgentSpan | OTelSpan) -> None:
        """Add an AgentSpan to the trace and clear the tokens_and_cost cache if present."""
        if not isinstance(span, AgentSpan):
            span = AgentSpan.from_otel(span)
        self.spans.append(span)
        self._invalidate_tokens_and_cost_cache()

    def add_spans(self, spans: list[AgentSpan]) -> None:
        """Add a list of AgentSpans to the trace and clear the tokens_and_cost cache if present."""
        self.spans.extend(spans)
        self._invalidate_tokens_and_cost_cache()

    def _convert_llm_message(
        self, msg: dict[str, Any], metadata: AssistantMessageMetadata
    ) -> AssistantMessage | None:
        """Convert an LLM output message dict to an AssistantMessage.

        Args:
            msg: Raw LLM message dict from OpenInference attributes.
            metadata: Per-span metadata (tokens, cost, latency) to attach.
        """

        role = msg.get("role")
        tool_calls = msg.get("tool_calls")

        if role in ["assistant", "model"]:  # model is used by Google ADK
            text_content = []

            # openinference support content as a string or a list of dicts
            # https://github.com/Arize-ai/openinference/blob/main/spec/multimodal_attributes.md
            content = msg.get("content")
            if content:
                if isinstance(content, str):
                    text_content = [MessageContentText(text=content)]

            contents = msg.get("contents")
            if contents and isinstance(contents, list):
                for content in contents:
                    if not isinstance(content, dict):
                        continue

                    message_content = content.get("message_content")
                    if not isinstance(message_content, dict):
                        continue

                    if message_content.get("type") == "text":
                        text_content.append(
                            MessageContentText(text=message_content.get("text"))
                        )

            tool_calls_list = None
            if tool_calls and isinstance(tool_calls, list):
                tool_calls_list = []
                for tc in tool_calls:
                    if not isinstance(tc, dict):
                        continue

                    function = tc.get("function", {})
                    if not isinstance(function, dict):
                        continue

                    tool_call_id = tc.get("id", "")
                    tool_name = function.get("name", "")
                    arguments_str = function.get("arguments", "")

                    # Parse arguments - could be JSON string or already a dict
                    arguments = {}
                    if arguments_str:
                        if isinstance(arguments_str, str):
                            try:
                                arguments = json.loads(arguments_str)
                            except (json.JSONDecodeError, TypeError):
                                arguments = {}
                        elif isinstance(arguments_str, dict):
                            arguments = arguments_str

                    tool_calls_list.append(
                        ToolCall(
                            id=tool_call_id,
                            name=tool_name,
                            arguments=arguments,
                        )
                    )

            return AssistantMessage(
                content=text_content if text_content else None,
                tool_calls=tool_calls_list if tool_calls_list else None,
                metadata=metadata,
            )

        return None

    def _convert_tool_message(self, msg: dict[str, Any]) -> ToolMessage | None:
        """Convert a tool message dict to a ToolMessage."""
        content = msg.get("response", "")

        return ToolMessage(
            tool_name=msg.get("tool_name"),
            tool_call_id=msg.get("tool_call_id"),
            content=[MessageContentText(type="text", text=str(content))],
        )

    def _extract_assistant_metadata(self, span: AgentSpan) -> AssistantMessageMetadata:
        """Extract assistant message metadata from a span.

        Args:
            span: The span to extract metadata from.

        Returns:
            AssistantMessageMetadata with tokens, cost, latency, and model info.
        """
        # Per-span token and cost metrics for assistant messages
        span_input_tokens = span.attributes.get(
            SpanAttributes.LLM_TOKEN_COUNT_PROMPT, 0
        )
        span_output_tokens = span.attributes.get(
            SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, 0
        )
        span_input_cost = span.attributes.get(SpanAttributes.LLM_COST_PROMPT, 0.0)
        span_output_cost = span.attributes.get(SpanAttributes.LLM_COST_COMPLETION, 0.0)

        # Per-span latency (nanoseconds as float)
        span_start_time = float(span.start_time) if span.start_time is not None else 0.0
        span_end_time = float(span.end_time) if span.end_time is not None else 0.0

        # Per-span model info
        span_model_name = span.attributes.get(SpanAttributes.LLM_MODEL_NAME, "")
        span_model_provider = span.attributes.get(SpanAttributes.LLM_PROVIDER, "")

        return AssistantMessageMetadata(
            tokens=MessageTokenInfo(
                input_tokens=span_input_tokens,
                output_tokens=span_output_tokens,
            ),
            cost=MessageCostInfo(
                input_cost=span_input_cost,
                output_cost=span_output_cost,
            ),
            latency=MessageLatencyInfo(
                start_time=span_start_time,
                end_time=span_end_time,
            ),
            model_info=MessageModelInfo(
                model_name=span_model_name,
                model_provider=span_model_provider,
            ),
        )

    def _extract_tool_metadata(self, span: AgentSpan) -> ToolMessageMetadata:
        """Extract tool message metadata from a span."""
        span_start_time = float(span.start_time) if span.start_time is not None else 0.0
        span_end_time = float(span.end_time) if span.end_time is not None else 0.0

        return ToolMessageMetadata(
            latency=MessageLatencyInfo(
                start_time=span_start_time,
                end_time=span_end_time,
            ),
        )

    def to_agent_trajectory(
        self,
        framework: Optional[Framework] = Framework.DEFAULT,
        only_leaf_llms: Optional[bool] = True,
    ) -> List[AssistantMessage | ToolMessage]:
        """
        Convert trace spans to agent trajectory.

        Args:
            framework: Agent framework to use for tool extraction
            only_leaf_llms: If True, only include LLM spans that have no LLM children

        Returns:
            List of AssistantMessage and ToolMessage in chronological order
        """
        # Framework-specific sorting:
        # - Some frameworks (pydantic_ai, agno) execute tools DURING the LLM span
        #   (tools are nested inside LLM), so we sort by end_time to get correct order
        #   This means the parent span does not end before the nested span ends.
        # - Other frameworks (langchain, openai_agents, etc.) execute tools AFTER the LLM span
        #   ends, so start_time sort works fine
        nested_tool_frameworks = (Framework.PYDANTIC_AI, Framework.AGNO)

        if framework in nested_tool_frameworks:
            # Sort by end_time: LLM output is ready at end_time, then tool results follow
            sorted_spans = sorted(
                self.spans,
                key=lambda s: s.end_time if s.end_time is not None else 0,
            )
        else:
            # Sort by start_time: LLM completes, then tools start after
            sorted_spans = sorted(
                self.spans,
                key=lambda s: s.start_time if s.start_time is not None else 0,
            )

        # Build parent-child relationships for only_leaf_llms filtering
        span_children: dict[str, list[str]] = {}
        llm_span_ids: set[str] = set()

        if only_leaf_llms:
            for span in sorted_spans:
                span_id = str(span.context.span_id) if span.context.span_id else None
                parent_id = (
                    str(span.parent.span_id)
                    if span.parent and span.parent.span_id
                    else None
                )

                if parent_id and parent_id != "null" and span_id:
                    if parent_id not in span_children:
                        span_children[parent_id] = []
                    span_children[parent_id].append(span_id)

                if span.is_llm_call() and span_id:
                    llm_span_ids.add(span_id)

        def has_llm_children(span_id: str) -> bool:
            """Check if a span has LLM children."""
            if not only_leaf_llms:
                return False
            children = span_children.get(span_id, [])
            return any(child_id in llm_span_ids for child_id in children)

        # Collect messages from spans
        messages: List[AssistantMessage | ToolMessage] = []

        for span in sorted_spans:
            span_id = str(span.context.span_id) if span.context.span_id else None

            if span.is_llm_call():
                # Skip if this LLM has LLM children (not a leaf)
                if only_leaf_llms and span_id and has_llm_children(span_id):
                    continue

                metadata = self._extract_assistant_metadata(span)

                for llm_msg in span.to_llm_messages():
                    converted = self._convert_llm_message(llm_msg, metadata=metadata)
                    if converted:
                        messages.append(converted)

            elif span.is_tool_execution():
                # Use span method to extract tool message
                tool_msg = span.to_tool_message(framework=framework)
                if tool_msg:
                    converted = self._convert_tool_message(tool_msg)
                    if converted:
                        converted.metadata = self._extract_tool_metadata(span)
                        messages.append(converted)

        return messages

    @cached_property
    def system_messages(self) -> List[SystemMessage]:
        """
        Extract unique system messages from all LLM spans in the trace.

        Returns:
            List of unique system messages from LLM input messages (deduplicated)
        """
        seen_messages = set()
        system_messages: List[SystemMessage] = []

        for span in self.spans:
            if span.is_llm_call():
                # Extract input messages
                unflattened = unflatten_messages(span.attributes)
                input_msgs = unflattened.get("llm.input_messages", [])

                # Filter for system messages
                for msg in input_msgs:
                    if isinstance(msg, dict) and msg.get("role") == "system":
                        if msg.get("content"):
                            prompt = msg.get("content")
                        elif msg.get("contents"):
                            contents = msg.get("contents")
                            if not contents:
                                continue

                            prompt = contents[0].get("message_content", {}).get("text")

                        # Use JSON string as hashable key for deduplication
                        msg_key = json.dumps(prompt, sort_keys=True)
                        if msg_key not in seen_messages:
                            seen_messages.add(msg_key)
                            system_messages.append(
                                SystemMessage(content=[MessageContentText(text=prompt)])
                            )

        return system_messages

    @cached_property
    def tokens(self) -> TokenInfo:
        """The [`TokenInfo`][any_agent.tracing.agent_trace.TokenInfo] for this trace. Cached after first computation."""
        sum_input_tokens = 0
        sum_output_tokens = 0
        for span in self.spans:
            if span.is_llm_call():
                sum_input_tokens += span.attributes.get(
                    SpanAttributes.LLM_TOKEN_COUNT_PROMPT, 0
                )
                sum_output_tokens += span.attributes.get(
                    SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, 0
                )
        return TokenInfo(input_tokens=sum_input_tokens, output_tokens=sum_output_tokens)

    @cached_property
    def cost(self) -> CostInfo:
        """The [`CostInfo`][any_agent.tracing.agent_trace.CostInfo] for this trace. Cached after first computation."""
        sum_input_cost = 0.0
        sum_output_cost = 0.0
        for span in self.spans:
            if span.is_llm_call():
                sum_input_cost += span.attributes.get(SpanAttributes.LLM_COST_PROMPT, 0)
                sum_output_cost += span.attributes.get(
                    SpanAttributes.LLM_COST_COMPLETION, 0
                )
        return CostInfo(input_cost=sum_input_cost, output_cost=sum_output_cost)
