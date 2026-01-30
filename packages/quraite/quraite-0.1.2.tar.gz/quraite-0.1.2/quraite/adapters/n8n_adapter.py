import asyncio
import json
import uuid
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


class N8nAdapter(BaseAdapter):
    def __init__(
        self, api_url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 60
    ):
        self.api_url = api_url
        self.headers = headers or {}
        self.timeout = timeout

        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
        logger.info(
            "N8nAdapter initialized (api_url=%s, timeout=%s)", self.api_url, timeout
        )

    def _convert_api_output_to_messages(
        self,
        response: Dict[str, Any],
    ) -> List[AgentMessage]:
        logger.debug(
            "Converting n8n response (steps=%d)",
            len(response[0].get("intermediateSteps", [])),
        )
        messages: List[AgentMessage] = []
        output = response[0]["output"]
        intermediateSteps = response[0]["intermediateSteps"]

        if not intermediateSteps:
            return [
                AssistantMessage(
                    content=[MessageContentText(type="text", text=output)],
                )
            ]

        def flush_messages(tool_calls_dict: Dict[str, Any]):
            nonlocal messages
            tool_calls_list: List[ToolCall] = []
            tool_results: List[ToolMessage] = []

            for tool_call_id, tool_call_dict in tool_calls_dict.items():
                tool_name = tool_call_dict.get("name", "")
                tool_args = tool_call_dict.get("arguments", {})
                if not isinstance(tool_args, dict):
                    tool_args = {}

                tool_calls_list.append(
                    ToolCall(
                        id=tool_call_id,
                        name=tool_name,
                        arguments=tool_args,
                    )
                )

                tool_result = tool_call_dict.get("result", "")
                tool_results.append(
                    ToolMessage(
                        tool_name=tool_name,
                        tool_call_id=tool_call_id,
                        content=[
                            MessageContentText(type="text", text=str(tool_result))
                        ],
                    )
                )

            if tool_calls_list:
                messages.append(AssistantMessage(tool_calls=tool_calls_list))

            messages.extend(tool_results)

        current_step_tool_calls_dict: Dict[str, Any] = {}
        for step in intermediateSteps:
            message_log = step.get("action", {}).get("messageLog", {})
            if message_log:
                tool_calls = message_log[0].get("kwargs", {}).get("tool_calls", [])

                if tool_calls:
                    # this condition means that we are at the start of a new step,
                    # so we need to flush the previous step's tool calls and tool results
                    if current_step_tool_calls_dict:
                        flush_messages(current_step_tool_calls_dict)
                        current_step_tool_calls_dict = {}

                    for tool_call in tool_calls:
                        current_step_tool_calls_dict[tool_call.get("id")] = {
                            "name": tool_call.get("name"),
                            "arguments": tool_call.get("args"),
                        }

            tool_id = step.get("action", {}).get("toolCallId")
            if tool_id not in current_step_tool_calls_dict:
                continue

            current_step_tool_calls_dict[tool_id]["result"] = step.get("observation")

        # flush the last step's tool calls and tool results
        flush_messages(current_step_tool_calls_dict)
        messages.append(
            AssistantMessage(
                content=[MessageContentText(type="text", text=output)],
            )
        )

        logger.info(
            "n8n conversion produced %d messages (final_output_length=%d)",
            len(messages),
            len(str(output)),
        )
        return messages

    def _prepare_input(self, input: List[AgentMessage]) -> str:
        logger.debug("Preparing n8n input from %d messages", len(input))
        if not input or input[-1].role != "user":
            logger.error("n8n input missing user message")
            raise ValueError("No user message found in the input")

        last_user_message = input[-1]
        if not last_user_message.content:
            logger.error("n8n user message missing content")
            raise ValueError("User message has no content")

        text_content = None
        for content_item in last_user_message.content:
            if content_item.type == "text" and content_item.text:
                text_content = content_item.text
                break

        if not text_content:
            logger.error("n8n user message missing text content")
            raise ValueError("No text content found in user message")

        logger.debug("Prepared n8n input (text_length=%d)", len(text_content))
        return text_content

    async def _aapi_call(
        self,
        query: str,
        sessionId: str,
    ) -> Dict[str, Any]:
        payload = {
            "query": query,
            "sessionId": sessionId,
        }
        logger.debug(
            "Calling n8n API (sessionId=%s, query_length=%d)", sessionId, len(query)
        )
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    response.raise_for_status()
                    logger.info("n8n API call succeeded (status=%s)", response.status)
                    return await response.json()

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.exception("n8n API request failed")
                raise aiohttp.ClientError(f"Async API request failed: {str(e)}") from e

            except json.JSONDecodeError as e:
                logger.exception("n8n API response decoding failed")
                raise ValueError(f"Failed to decode JSON response: {e}") from e

    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Union[str, None],
    ) -> AgentInvocationResponse:
        logger.info(
            "n8n ainvoke called (session_id=%s, input_messages=%d)",
            session_id,
            len(input),
        )
        agent_input = self._prepare_input(input)

        try:
            agent_output = await self._aapi_call(
                query=agent_input,
                sessionId=session_id if session_id else uuid.uuid4(),
            )
            logger.debug(
                "n8n API returned payload keys: %s", list(agent_output[0].keys())
            )
        except Exception as e:
            logger.exception("Error calling n8n endpoint")
            raise RuntimeError(f"Error calling n8n endpoint: {e}") from e

        try:
            agent_trajectory = self._convert_api_output_to_messages(agent_output)
            logger.info(
                "n8n conversion produced %d trajectory messages", len(agent_trajectory)
            )
            return AgentInvocationResponse(
                agent_trajectory=agent_trajectory,
            )
        except Exception as e:
            logger.exception("Error processing n8n response")
            raise RuntimeError(f"Error processing n8n response: {e}") from e
