from typing import Any, List, Literal, Optional, TypeAlias, Union

from pydantic import BaseModel, Field


class MessageContentText(BaseModel):
    type: Literal["text"] = "text"
    text: str


class MessageContentReasoning(BaseModel):
    type: Literal["reasoning"] = "reasoning"
    reasoning: str


class UserMessage(BaseModel):
    role: Literal["user"] = "user"
    name: Optional[str] = None
    content: List[MessageContentText]


class DeveloperMessage(BaseModel):
    role: Literal["developer"] = "developer"
    content: List[MessageContentText]


class SystemMessage(BaseModel):
    role: Literal["system"] = "system"
    content: List[MessageContentText]


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class ModelInfo(BaseModel):
    model_name: str = Field(default="")
    model_provider: str = Field(default="")


class CostInfo(BaseModel):
    input_cost: float = Field(default=0.0)
    output_cost: float = Field(default=0.0)


class TokenInfo(BaseModel):
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)


class LatencyInfo(BaseModel):
    start_time: float = Field(default=0.0)
    end_time: float = Field(default=0.0)


class AssistantMessageMetadata(BaseModel):
    """Structured metadata for assistant messages."""

    tokens: TokenInfo = Field(default_factory=TokenInfo)
    cost: CostInfo = Field(default_factory=CostInfo)
    latency: LatencyInfo = Field(default_factory=LatencyInfo)
    model_info: ModelInfo = Field(default_factory=ModelInfo)


class ToolMessageMetadata(BaseModel):
    """Structured metadata for tool messages."""

    latency: LatencyInfo = Field(default_factory=LatencyInfo)


class AssistantMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    agent_name: Optional[str] = None
    content: Optional[List[Union[MessageContentText, MessageContentReasoning]]] = None
    tool_calls: Optional[List[ToolCall]] = None
    metadata: AssistantMessageMetadata = Field(default_factory=AssistantMessageMetadata)


class ToolMessage(BaseModel):
    role: Literal["tool"] = "tool"
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None
    content: List[MessageContentText]
    metadata: ToolMessageMetadata = Field(default_factory=ToolMessageMetadata)


AgentMessage: TypeAlias = Union[
    UserMessage, DeveloperMessage, SystemMessage, AssistantMessage, ToolMessage
]
