import asyncio
import json
import uuid
from typing import Any, Dict, List, Union

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


class LangflowAdapter(BaseAdapter):
    def __init__(self, api_url: str, x_api_key: str, timeout: int = 60):
        self.api_url = api_url
        self.x_api_key = x_api_key
        self.headers = {"Content-Type": "application/json", "x-api-key": self.x_api_key}
        self.timeout = timeout
        logger.info(
            "LangflowAdapter initialized (api_url=%s, timeout=%s)",
            self.api_url,
            timeout,
        )

    def _convert_api_output_to_messages(
        self,
        response: Dict[str, Any],
    ) -> List[AgentMessage]:
        logger.debug(
            "Converting Langflow response (root_keys=%s)",
            list(response.keys()),
        )
        content_blocks = response["outputs"][0]["outputs"][0]["results"]["message"][
            "content_blocks"
        ]
        contents = content_blocks[0]["contents"]

        # Assume everything sequential.
        ai_trajectory: List[AgentMessage] = []
        for step in contents:
            if step["type"] == "text":
                if step["header"]["title"] == "Input":
                    continue
                else:
                    ai_trajectory.append(
                        AssistantMessage(
                            content=[
                                MessageContentText(type="text", text=step["text"])
                            ],
                        )
                    )
            elif step["type"] == "tool_use":
                tool_id = str(uuid.uuid4())
                tool_input = step.get("tool_input", {})
                if not isinstance(tool_input, dict):
                    tool_input = {"value": tool_input}

                # Create AssistantMessage with tool call
                ai_trajectory.append(
                    AssistantMessage(
                        tool_calls=[
                            ToolCall(
                                id=tool_id,
                                name=step["name"],
                                arguments=tool_input,
                            )
                        ],
                    )
                )
                # Create ToolMessage with tool result
                tool_output = step.get("output", "")
                ai_trajectory.append(
                    ToolMessage(
                        tool_name=step["name"],
                        tool_call_id=tool_id,
                        content=[
                            MessageContentText(type="text", text=str(tool_output))
                        ],
                    )
                )

        logger.info(
            "Converted Langflow response into %d trajectory messages",
            len(ai_trajectory),
        )
        return ai_trajectory

    def _prepare_input(self, input: List[AgentMessage]) -> str:
        logger.debug("Preparing Langflow input from %d messages", len(input))
        if not input or input[-1].role != "user":
            logger.error("Langflow input missing user message")
            raise ValueError("No user message found in the input")

        last_user_message = input[-1]
        if not last_user_message.content:
            logger.error("Langflow input user message missing content")
            raise ValueError("User message has no content")

        text_content = None
        for content_item in last_user_message.content:
            if content_item.type == "text" and content_item.text:
                text_content = content_item.text
                break

        if not text_content:
            logger.error("Langflow input missing text content")
            raise ValueError("No text content found in user message")

        logger.debug("Prepared Langflow input (text_length=%d)", len(text_content))
        return text_content

    async def _aapi_call(
        self,
        query: str,
        sessionId: str,
    ) -> Dict[str, Any]:
        payload = {
            "output_type": "chat",
            "input_type": "chat",
            "input_value": query,
            "session_id": sessionId,
        }

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
                        "Langflow API call succeeded (status=%s)", response.status
                    )
                    return await response.json()

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.exception("Langflow API request failed")
                raise aiohttp.ClientError(f"Async API request failed: {str(e)}") from e

            except json.JSONDecodeError as e:
                logger.exception("Langflow API response decoding failed")
                raise ValueError(f"Failed to decode JSON response: {e}") from e

    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Union[str, None],
    ) -> AgentInvocationResponse:
        """Asynchronous invocation method - invokes the Langflow agent and converts to List[AgentMessage]."""
        logger.info(
            "Langflow ainvoke called (session_id=%s, input_messages=%d)",
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
                "Langflow API returned payload with top-level keys: %s",
                list(agent_output.keys()),
            )
        except Exception as e:
            logger.exception("Error calling Langflow endpoint")
            raise RuntimeError(f"Error calling langflow endpoint: {e}") from e

        try:
            agent_trajectory = self._convert_api_output_to_messages(agent_output)
            logger.info(
                "Langflow conversion produced %d trajectory messages",
                len(agent_trajectory),
            )
            return AgentInvocationResponse(
                agent_trajectory=agent_trajectory,
            )
        except Exception as e:
            logger.exception("Error processing Langflow response")
            raise RuntimeError(f"Error processing langflow response: {e}") from e
