import asyncio
import json
from typing import Any, Dict, List, Optional, Union

import aiohttp

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

logger = get_logger(__name__)


class FlowiseAdapter(BaseAdapter):
    def __init__(
        self, api_url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 60
    ):
        self.api_url = api_url
        self.headers = headers or {}
        self.timeout = timeout

        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"

        self.headers["Content-Type"] = "application/json"
        logger.info(
            "FlowiseAdapter initialized (api_url=%s, timeout=%s)", self.api_url, timeout
        )

    AGENT_NODE_NAME = "agentAgentflow"

    def _convert_api_output_to_messages(
        self,
        response: Dict[str, Any],
        request_messages: Optional[List[AgentMessage]] = None,
    ) -> List[AgentMessage]:
        logger.debug(
            "Converting Flowise response to messages (has_agent_node=%s)",
            bool(response.get("agentFlowExecutedData")),
        )

        def _append_text(content_obj: Any, bucket: List[MessageContentText]) -> None:
            if isinstance(content_obj, str):
                if content_obj:
                    bucket.append(MessageContentText(type="text", text=content_obj))
            elif isinstance(content_obj, list):
                for item in content_obj:
                    _append_text(item, bucket)
            elif isinstance(content_obj, dict):
                text_value = content_obj.get("text")
                if text_value:
                    bucket.append(MessageContentText(type="text", text=text_value))

        agent_node = self._find_agentflow_node(response)
        if agent_node:
            converted: List[AgentMessage] = []
            messages_section = agent_node.get("input")
            raw_messages = []
            if isinstance(messages_section, dict):
                potential_messages = messages_section.get("messages")
                if isinstance(potential_messages, list):
                    raw_messages = potential_messages

            latest_turn: List[Dict[str, Any]] = []
            for raw in reversed(raw_messages):
                if not isinstance(raw, dict):
                    continue
                if raw.get("role") == "user":
                    break
                latest_turn.append(raw)
            latest_turn.reverse()

            for raw in latest_turn:
                role = raw.get("role")
                if role not in {"assistant", "system", "tool"}:
                    continue

                if role == "assistant":
                    text_content: List[MessageContentText] = []
                    _append_text(raw.get("content"), text_content)
                    tool_calls_list: List[ToolCall] = []
                    tool_calls = raw.get("tool_calls")
                    if isinstance(tool_calls, list):
                        for call in tool_calls:
                            if not isinstance(call, dict):
                                continue
                            arguments = call.get("args")
                            if not isinstance(arguments, dict):
                                arguments = {"value": arguments}
                            tool_calls_list.append(
                                ToolCall(
                                    id=call.get("id"),
                                    name=call.get("name"),
                                    arguments=arguments,
                                )
                            )

                    converted.append(
                        AssistantMessage(
                            content=text_content if text_content else None,
                            tool_calls=tool_calls_list if tool_calls_list else None,
                        )
                    )

                elif role == "tool":
                    payload = raw.get("content")
                    tool_result = (
                        payload if isinstance(payload, dict) else {"output": payload}
                    )
                    converted.append(
                        ToolMessage(
                            tool_name=raw.get("name"),
                            tool_call_id=raw.get("tool_call_id"),
                            content=[
                                MessageContentText(
                                    type="text", text=json.dumps(tool_result)
                                )
                            ],
                        )
                    )

            output_section = agent_node.get("output")
            if isinstance(output_section, dict):
                final_segments: List[MessageContentText] = []
                _append_text(output_section.get("content"), final_segments)

                if final_segments:
                    converted.append(AssistantMessage(content=final_segments))

            if converted:
                return converted

        if request_messages:
            logger.debug("Falling back to request messages; no agent output found")
            return list(request_messages)

        return []

    def _find_agentflow_node(
        self, response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        executed_data = response.get("agentFlowExecutedData")
        if not isinstance(executed_data, list):
            return None

        for entry in executed_data:
            node_data = entry.get("data")
            if not isinstance(node_data, dict):
                continue

            if node_data.get("name") == self.AGENT_NODE_NAME:
                return node_data

        return None

    def _prepare_input(self, input: List[AgentMessage]) -> str:
        logger.debug("Preparing Flowise input from %d messages", len(input))
        if not input or input[-1].role != "user":
            logger.error("Flowise input missing user message")
            raise ValueError("No user message found in the input")

        last_user_message = input[-1]
        if not last_user_message.content:
            logger.error("Flowise input user message missing content")
            raise ValueError("User message has no content")

        text_content = None
        for content_item in last_user_message.content:
            if content_item.type == "text" and content_item.text:
                text_content = content_item.text
                break

        if not text_content:
            logger.error("Flowise input missing text content")
            raise ValueError("No text content found in user message")

        logger.debug("Prepared Flowise input (text_length=%d)", len(text_content))
        return text_content

    async def _aapi_call(
        self,
        question: str,
        history: Optional[List[Dict[str, Any]]] = None,
        override_config: Optional[Dict[str, Any]] = None,
        form: Optional[Dict[str, Any]] = None,
        human_input: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        logger.debug(
            "Calling Flowise API (history=%s, form=%s, human_input=%s)",
            bool(history),
            bool(form),
            bool(human_input),
        )
        payload = {
            "question": question,
            "overrideConfig": override_config or {},
            **kwargs,
        }

        if history is not None:
            payload["history"] = history

        if form is not None:
            payload["form"] = form

        if human_input is not None:
            payload["humanInput"] = human_input

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    response.raise_for_status()
                    logger.info(
                        "Flowise API call succeeded (status=%s)", response.status
                    )
                    return await response.json()

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.exception("Flowise API request failed")
                raise aiohttp.ClientError(f"Async API request failed: {str(e)}") from e

            except json.JSONDecodeError as e:
                logger.exception("Flowise API response decoding failed")
                raise ValueError(f"Failed to decode JSON response: {e}") from e

    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Union[str, None],
    ) -> AgentInvocationResponse:
        """Asynchronous invocation method - invokes the Flowise agent and converts to List[AgentMessage]."""
        logger.info(
            "Flowise ainvoke called (session_id=%s, input_messages=%d)",
            session_id,
            len(input),
        )
        agent_input = self._prepare_input(input)

        try:
            agent_output = await self._aapi_call(
                question=agent_input,
                override_config={"sessionId": session_id} if session_id else None,
            )
            logger.debug(
                "Flowise API returned payload with keys: %s", list(agent_output.keys())
            )
        except Exception as e:
            logger.exception("Flowise ainvoke failed during API call")
            raise RuntimeError(f"Error calling Flowise endpoint: {e}") from e

        try:
            agent_trajectory = self._convert_api_output_to_messages(agent_output, input)
            logger.info(
                "Flowise conversion produced %d trajectory messages",
                len(agent_trajectory),
            )
            return AgentInvocationResponse(
                agent_trajectory=agent_trajectory,
            )
        except Exception as e:
            logger.exception("Flowise ainvoke failed while processing response")
            raise RuntimeError(f"Error processing Flowise response: {e}") from e
