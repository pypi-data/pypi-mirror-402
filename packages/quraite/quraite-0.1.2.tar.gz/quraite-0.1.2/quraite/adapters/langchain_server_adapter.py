from __future__ import annotations

from typing import Annotated, Any, List, Optional, Union

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.pregel.remote import RemoteGraph
from langgraph_sdk import get_client, get_sync_client
from pydantic import Discriminator

from quraite.adapters.base import BaseAdapter
from quraite.logger import get_logger
from quraite.schema.message import AgentMessage, AssistantMessage, MessageContentText
from quraite.schema.message import SystemMessage as QuraiteSystemMessage
from quraite.schema.message import ToolCall, ToolMessage, UserMessage
from quraite.schema.response import AgentInvocationResponse

LangchainMessage = Annotated[
    Union[HumanMessage, SystemMessage, AIMessage, ToolMessage],
    Discriminator(discriminator="type"),
]

logger = get_logger(__name__)


class LangchainServerAdapter(BaseAdapter):
    """Remote LangChain server adapter based on langgraph-sdk.

    Args:
        base_url: The base URL of the LangChain server
        assistant_id: The ID of the assistant to invoke
        **kwargs: Additional keyword arguments passed directly to
                 langgraph_sdk.get_client() and get_sync_client().
                 Common options include:
                 - api_key: API key for authentication
                 - headers: Additional HTTP headers
                 - timeout: Request timeout configuration
    """

    def __init__(
        self,
        *,
        base_url: str,
        assistant_id: Optional[str] = None,
        graph_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        self.base_url = base_url
        self.assistant_id = assistant_id
        self.graph_name = graph_name

        logger.debug(
            "Initializing LangchainServerAdapter (base_url=%s, assistant_id=%s, graph_name=%s)",
            base_url,
            assistant_id,
            graph_name,
        )
        try:
            sync_client = get_sync_client(url=self.base_url, **kwargs)
            async_client = get_client(url=self.base_url, **kwargs)
            if self.assistant_id:
                self.remote_graph = RemoteGraph(
                    self.assistant_id,
                    url=self.base_url,
                    sync_client=sync_client,
                    client=async_client,
                )
            else:
                self.remote_graph = RemoteGraph(
                    self.graph_name,
                    url=self.base_url,
                    sync_client=sync_client,
                    client=async_client,
                )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialize LangChain RemoteGraph for {self.base_url}: {exc}"
            )
        logger.info(
            "LangchainServerAdapter initialized (assistant_id=%s, graph_name=%s)",
            self.assistant_id,
            self.graph_name,
        )

    def _prepare_input(self, input: List[AgentMessage]) -> Any:
        """
        Prepare input for LangChain agent from List[AgentMessage].

        Args:
            input: List[AgentMessage] containing user_message

        Returns:
            Dict with messages list containing user_message
        """
        logger.debug("Preparing Langchain server input from %d messages", len(input))
        if not input or input[-1].role != "user":
            logger.error("Langchain server input missing user message")
            raise ValueError("No user message found in the input")

        last_user_message = input[-1]
        # Check if content list is not empty and has text
        if not last_user_message.content:
            logger.error("Langchain server user message missing content")
            raise ValueError("User message has no content")

        # Find the first text content item
        text_content = None
        for content_item in last_user_message.content:
            if content_item.type == "text" and content_item.text:
                text_content = content_item.text
                break

        if not text_content:
            logger.error("Langchain server user message missing text content")
            raise ValueError("No text content found in user message")

        logger.debug(
            "Prepared Langchain server input (text_length=%d)", len(text_content)
        )
        return {"messages": [HumanMessage(content=text_content).model_dump()]}

    def _convert_langchain_messages_to_quraite_messages(
        self,
        messages: List[dict],
    ) -> List[AgentMessage]:
        logger.debug(
            "Converting %d Langchain server messages to quraite format", len(messages)
        )
        converted_messages: List[AgentMessage] = []

        for msg in messages:
            if msg.get("type") == "system":
                converted_messages.append(
                    QuraiteSystemMessage(
                        content=[
                            MessageContentText(type="text", text=msg.get("content", ""))
                        ],
                    )
                )

            elif msg.get("type") == "human":
                converted_messages.append(
                    UserMessage(
                        content=[
                            MessageContentText(type="text", text=msg.get("content", ""))
                        ],
                    )
                )

            elif msg.get("type") == "ai":
                text_content: List[MessageContentText] = []
                tool_calls_list: List[ToolCall] = []

                # Extract text content - sometimes it's a string, sometimes a list of dicts
                content = msg.get("content")
                if isinstance(content, str) and content:
                    text_content.append(MessageContentText(type="text", text=content))
                elif isinstance(content, list):
                    for content_item in content:
                        if isinstance(content_item, dict):
                            if content_item.get("type") == "text" and content_item.get(
                                "text"
                            ):
                                text_content.append(
                                    MessageContentText(
                                        type="text", text=content_item.get("text")
                                    )
                                )

                # Extract tool calls if present
                if msg.get("tool_calls"):
                    for tool_call in msg.get("tool_calls"):
                        if isinstance(tool_call, dict):
                            tool_calls_list.append(
                                ToolCall(
                                    id=tool_call.get("id", ""),
                                    name=tool_call.get("name", ""),
                                    arguments=tool_call.get("args", {}),
                                )
                            )

                converted_messages.append(
                    AssistantMessage(
                        content=text_content if text_content else None,
                        tool_calls=tool_calls_list if tool_calls_list else None,
                    )
                )

            elif msg.get("type") == "tool":
                tool_content = msg.get("content", "")
                converted_messages.append(
                    ToolMessage(
                        tool_call_id=msg.get("tool_call_id", ""),
                        content=[
                            MessageContentText(type="text", text=str(tool_content))
                        ],
                    )
                )

            else:
                # Skip unsupported message types
                continue

        logger.info(
            "Langchain server message conversion produced %d messages",
            len(converted_messages),
        )
        return converted_messages

    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Annotated[Union[str, None], "Thread ID used by LangChain API"],
    ) -> AgentInvocationResponse:
        agent_messages = []
        agent_input = self._prepare_input(input)
        if session_id:
            config = {"configurable": {"thread_id": session_id}}
        else:
            config = {}

        try:
            logger.info("Langchain server ainvoke called (session_id=%s)", session_id)
            async for event in self.remote_graph.astream(agent_input, config=config):
                for _, result in event.items():
                    if result.get("messages"):
                        logger.debug(
                            "Langchain server received %d messages from stream chunk",
                            len(result.get("messages")),
                        )
                        agent_messages += result.get("messages")

        except Exception as e:
            logger.exception("Error invoking Langchain remote graph")
            raise RuntimeError(f"Error invoking LangChain agent: {e}") from e

        try:
            # Convert to List[AgentMessage]
            agent_trajectory = self._convert_langchain_messages_to_quraite_messages(
                agent_messages
            )
            logger.info(
                "Langchain server ainvoke produced %d trajectory messages",
                len(agent_trajectory),
            )

            return AgentInvocationResponse(
                agent_trajectory=agent_trajectory,
            )

        except ValueError:
            logger.exception("Langchain server conversion to AgentMessage failed")
            return AgentInvocationResponse()
