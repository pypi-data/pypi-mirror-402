"""
Framework-specific tool extractors for converting span attributes to standardized tool call information.

These extractors handle the varying attribute structures across different agent frameworks
(pydantic, langchain, adk, openai_agents, agno, smolagents, etc.)
"""

import json
from typing import Any, Protocol

from openinference.semconv.trace import SpanAttributes

from quraite.tracing.constants import Framework


class ToolCallInfo:
    """Standardized tool call information extracted from a TOOL span."""

    def __init__(
        self,
        tool_name: str,
        tool_call_id: str | None,
        arguments: str | dict,
        response: Any,
    ):
        self.tool_name = tool_name
        self.tool_call_id = tool_call_id
        self.arguments = arguments
        self.response = response

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_name": self.tool_name,
            "tool_call_id": self.tool_call_id,
            "arguments": self.arguments,
            "response": self.response,
        }


class ToolExtractor(Protocol):
    """Protocol for framework-specific tool extractors."""

    def __call__(self, span: dict[str, Any]) -> ToolCallInfo | None: ...


# =============================================================================
# Framework-specific tool extractors
# =============================================================================


def extract_tool_pydantic(span: dict[str, Any]) -> ToolCallInfo | None:
    """
    Extract tool info from Pydantic AI tool spans.

    Attributes:
        - tool.name: "customer_balance"
        - tool_call.id: "call_xxx"
        - tool_arguments: "{\"include_pending\":true}"
        - tool_response: "$123.45"
    """
    attrs = span.get("attributes", {})

    tool_name = attrs.get("tool.name") or attrs.get("gen_ai.tool.name")
    if not tool_name:
        return None

    tool_call_id = attrs.get("tool_call.id") or attrs.get("gen_ai.tool.call.id")
    arguments = attrs.get("tool_arguments", "{}")
    response = attrs.get("tool_response", "")

    return ToolCallInfo(
        tool_name=tool_name,
        tool_call_id=tool_call_id,
        arguments=arguments,
        response=response,
    )


def extract_tool_langchain(span: dict[str, Any]) -> ToolCallInfo | None:
    """
    Extract tool info from LangChain tool spans.

    Attributes:
        - tool.name: "add"
        - tool.description: "Add two numbers."
        - input.value: "{'b': 1, 'a': 1}"
        - output.value: JSON with content
    """
    attrs = span.get("attributes", {})

    tool_name = attrs.get("tool.name")
    if not tool_name:
        return None

    arguments = attrs.get("input.value", "{}")
    output_value = attrs.get("output.value", "")

    # Also check for response attribute (some LangChain spans store response here)
    response_value = attrs.get("response", output_value)

    # Try to parse output to extract content
    response = response_value
    if isinstance(response_value, str):
        try:
            parsed = json.loads(response_value)
            if isinstance(parsed, dict):
                # Check if response field contains JSON string (nested JSON)
                if "response" in parsed and isinstance(parsed["response"], str):
                    try:
                        inner_parsed = json.loads(parsed["response"])
                        if isinstance(inner_parsed, dict) and "update" in inner_parsed:
                            parsed = inner_parsed
                    except (json.JSONDecodeError, TypeError):
                        pass

                # First check for direct content field
                if "content" in parsed:
                    response = parsed.get("content", response_value)
                # Check for update.messages structure (LangChain graph updates)
                # this comes when you use supervisor agent with multiple agents
                elif "update" in parsed:
                    update = parsed.get("update", {})
                    messages = update.get("messages", [])
                    # Find the last tool message
                    for msg in reversed(messages):
                        if isinstance(msg, dict) and msg.get("type") == "tool":
                            content = msg.get("content", "")
                            if content:
                                response = content
                                break
                    else:
                        # No tool message found, keep original response
                        response = response_value
                else:
                    response = response_value
        except json.JSONDecodeError:
            pass

    return ToolCallInfo(
        tool_name=tool_name,
        tool_call_id=None,  # LangChain doesn't always have call IDs in tool spans
        arguments=arguments,
        response=response,
    )


def extract_tool_adk(span: dict[str, Any]) -> ToolCallInfo | None:
    """
    Extract tool info from Google ADK tool spans.

    Attributes:
        - tool.name: "get_weather"
        - tool.parameters: "{\"city\": \"New York\"}"
        - gcp.vertex.agent.tool_call_args: "{\"city\": \"New York\"}"
        - gcp.vertex.agent.tool_response: JSON response
        - output.value: JSON with id, name, response
    """
    attrs = span.get("attributes", {})

    tool_name = attrs.get("tool.name") or attrs.get("gen_ai.tool.name")
    if not tool_name:
        return None

    # Skip merged tool spans
    if tool_name == "(merged tools)":
        return None

    tool_call_id = attrs.get("gen_ai.tool.call.id")
    arguments = (
        attrs.get("tool.parameters")
        or attrs.get("gcp.vertex.agent.tool_call_args")
        or attrs.get("input.value", "{}")
    )

    # Get response from various possible locations
    response = attrs.get("gcp.vertex.agent.tool_response", "")
    if not response or response == "<not serializable>":
        output_value = attrs.get("output.value", "")
        if isinstance(output_value, str):
            try:
                parsed = json.loads(output_value)
                if isinstance(parsed, dict) and "response" in parsed:
                    response = parsed.get("response", output_value)
                else:
                    response = output_value
            except json.JSONDecodeError:
                response = output_value
        else:
            response = output_value

    return ToolCallInfo(
        tool_name=tool_name,
        tool_call_id=tool_call_id,
        arguments=arguments,
        response=response,
    )


def extract_tool_openai_agents(span: dict[str, Any]) -> ToolCallInfo | None:
    """
    Extract tool info from OpenAI Agents tool spans.

    Attributes:
        - tool.name: "multiply"
        - input.value: "{\"a\":10,\"b\":2}"
        - output.value: 20.0
    """
    attrs = span.get("attributes", {})

    tool_name = attrs.get("tool.name")
    if not tool_name:
        return None

    arguments = attrs.get("input.value", "{}")
    response = attrs.get("output.value", "")

    return ToolCallInfo(
        tool_name=tool_name,
        tool_call_id=None,  # OpenAI Agents SDK doesn't put call ID in tool span
        arguments=arguments,
        response=response,
    )


def extract_tool_agno(span: dict[str, Any]) -> ToolCallInfo | None:
    """
    Extract tool info from Agno tool spans.

    Attributes:
        - tool.name: "duckduckgo_search"
        - tool.description: "..."
        - tool.parameters: "{\"query\": \"...\", \"max_results\": 5}"
        - input.value: same as parameters
        - output.value: JSON response
    """
    attrs = span.get("attributes", {})

    tool_name = attrs.get("tool.name")
    if not tool_name:
        return None

    arguments = attrs.get("tool.parameters") or attrs.get("input.value", "{}")
    response = attrs.get("output.value", "")

    return ToolCallInfo(
        tool_name=tool_name,
        tool_call_id=None,
        arguments=arguments,
        response=response,
    )


def extract_tool_smolagents(span: dict[str, Any]) -> ToolCallInfo | None:
    """
    Extract tool info from SmolAgents tool spans.
    """
    attrs = span.get("attributes", {})

    tool_name = attrs.get("tool.name")
    if not tool_name:
        return None

    arguments = attrs.get("input.value", "{}")
    response = attrs.get("output.value", "")

    return ToolCallInfo(
        tool_name=tool_name,
        tool_call_id=None,
        arguments=arguments,
        response=response,
    )


def extract_default(span: dict[str, Any]) -> ToolCallInfo | None:
    """
    Extract tool info following openinference semantic conventions.
    """
    attrs = span.get("attributes", {})

    tool_name = attrs.get(SpanAttributes.TOOL_NAME, "")
    arguments = attrs.get(SpanAttributes.TOOL_PARAMETERS, "{}")
    response = attrs.get(SpanAttributes.OUTPUT_VALUE, "")

    return ToolCallInfo(
        tool_name=tool_name,
        tool_call_id=None,
        arguments=arguments,
        response=response,
    )


# Registry of framework extractors
TOOL_EXTRACTORS: dict[Framework, ToolExtractor] = {
    Framework.PYDANTIC_AI: extract_tool_pydantic,
    Framework.LANGCHAIN: extract_tool_langchain,
    Framework.GOOGLE_ADK: extract_tool_adk,
    Framework.OPENAI_AGENTS: extract_tool_openai_agents,
    Framework.AGNO: extract_tool_agno,
    Framework.SMOLAGENTS: extract_tool_smolagents,
    Framework.DEFAULT: extract_default,
}


def get_tool_extractor(framework: Framework | str) -> ToolExtractor:
    """Get the appropriate tool extractor for the given framework."""
    if isinstance(framework, str):
        framework = Framework(framework.lower())
    return TOOL_EXTRACTORS.get(framework, extract_default)
