"""
Bedrock Agents Adapter
https://docs.aws.amazon.com/bedrock/latest/userguide/trace-events.html
"""

import asyncio
import json
import os
import uuid
from typing import Any, Dict, List, Optional, Union

import boto3
from botocore.exceptions import ClientError

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


class BedrockAgentsAdapter(BaseAdapter):
    """
    Bedrock Agents adapter wrapper that converts AWS Bedrock agent
    to a standardized callable interface (invoke) and converts the output to List[AgentMessage].

    This class wraps any Bedrock Agent and provides:
    - Synchronous invocation via invoke()
    - Automatic conversion to List[AgentMessage] format
    """

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        agent_id: Optional[str] = None,
        agent_alias_id: Optional[str] = None,
        region_name: Optional[str] = None,
        agent_name: str = "Bedrock Agent",
    ):
        """
        Initialize with Bedrock agent configuration

        Args:
            aws_access_key_id: AWS access key ID (defaults to AWS_ACCESS_KEY_ID env var)
            aws_secret_access_key: AWS secret access key (defaults to AWS_SECRET_ACCESS_KEY env var)
            aws_session_token: AWS session token (defaults to AWS_SESSION_TOKEN env var)
            agent_id: Bedrock agent ID (defaults to BEDROCK_AGENT_ID env var)
            agent_alias_id: Bedrock agent alias ID (defaults to BEDROCK_AGENT_ALIAS_ID env var)
            region_name: AWS region (defaults to AWS_REGION env var)
            agent_name: Name of the agent for trajectory metadata
        """
        logger.debug(
            "Initializing BedrockAgentsAdapter (agent_name=%s, region=%s)",
            agent_name,
            region_name or os.getenv("AWS_REGION"),
        )
        self.agent_id = agent_id or os.getenv("BEDROCK_AGENT_ID")
        self.agent_alias_id = agent_alias_id or os.getenv("BEDROCK_AGENT_ALIAS_ID")
        self.region_name = region_name or os.getenv("AWS_REGION")
        self.agent_name = agent_name

        if not all([self.agent_id, self.agent_alias_id, self.region_name]):
            raise ValueError(
                "Missing required configuration. Please provide agent_id, agent_alias_id, "
                "and region_name either as parameters or environment variables."
            )

        # Initialize Bedrock client
        self.bedrock_client = boto3.client(
            region_name=self.region_name,
            aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_access_key
            or os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=aws_session_token or os.getenv("AWS_SESSION_TOKEN"),
            service_name="bedrock-agent-runtime",
        )
        logger.info(
            "BedrockAgentsAdapter initialized (agent_id=%s, alias=%s, region=%s)",
            self.agent_id,
            self.agent_alias_id,
            self.region_name,
        )

    def _convert_bedrock_traces_to_messages(
        self,
        traces: List[Dict[str, Any]],
    ) -> List[AgentMessage]:
        logger.debug("Converting %d Bedrock trace events to messages", len(traces))
        if not traces:
            return []

        # TODO: Handle agents with only knowledge base
        # It has a modelInvocationInput with KNOWLEDGE_BASE_RESPONSE_GENERATION that
        # has a system prompt. Discuss and decide how to handle this.

        messages = []
        for trace in traces:
            # TODO: handle other trace types as well - https://docs.aws.amazon.com/bedrock/latest/userguide/trace-events.html#trace-understand
            orchestration_trace = trace.get("trace", {}).get("orchestrationTrace", {})
            if not orchestration_trace:
                continue

            if "modelInvocationOutput" in orchestration_trace:
                model_invocation_output = orchestration_trace["modelInvocationOutput"]

                raw_response_content = model_invocation_output.get(
                    "rawResponse", {}
                ).get("content", "")
                if not raw_response_content:
                    continue

                try:
                    parsed_content = json.loads(raw_response_content)
                    contents = parsed_content.get("content", [])
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.exception("Error parsing Bedrock raw response content")

                if not contents:
                    continue

                text_content = []
                tool_calls = []
                for content in contents:
                    if content.get("type") == "text":
                        text_content.append(
                            MessageContentText(
                                type="text", text=content.get("text", "")
                            )
                        )
                    # TODO: Revsist this later. Ideally should use this but the tool_call_id does not come in the invocationInput
                    # so for now using trace_id as the tool_call_id
                    # elif content.get("type") == "tool_use":
                    #     tool_calls.append(
                    #         ToolCall(
                    #             id=content.get("id", ""),
                    #             name=content.get("name", ""),
                    #             arguments=content.get("input", {}),
                    #         )
                    #     )

                messages.append(
                    AssistantMessage(
                        content=text_content if text_content else None,
                        tool_calls=tool_calls if tool_calls else None,
                    )
                )
            elif "invocationInput" in orchestration_trace:
                invocation_input = orchestration_trace["invocationInput"]
                if invocation_input.get("invocationType") == "KNOWLEDGE_BASE":
                    kb_input = invocation_input.get("knowledgeBaseLookupInput", {})
                    tool_call = ToolCall(
                        id=invocation_input.get("traceId", ""),
                        name="knowledge_base_lookup",
                        arguments={
                            "text": kb_input.get("text", ""),
                            "knowledgeBaseId": kb_input.get("knowledgeBaseId", ""),
                        },
                    )

                    if messages and isinstance(messages[-1], AssistantMessage):
                        if messages[-1].tool_calls:
                            messages[-1].tool_calls.append(tool_call)
                        else:
                            messages[-1].tool_calls = [tool_call]
                    else:
                        messages.append(AssistantMessage(tool_calls=[tool_call]))

                elif invocation_input.get("invocationType") == "ACTION_GROUP":
                    action_group_input = invocation_input.get(
                        "actionGroupInvocationInput", {}
                    )
                    tool_call = ToolCall(
                        id=invocation_input.get("traceId", ""),
                        name=f"{action_group_input.get('actionGroupName', '')}/{action_group_input.get('function', '')}",
                        arguments={
                            p["name"]: p["value"]
                            for p in action_group_input.get("parameters", [])
                        },
                    )
                    messages.append(AssistantMessage(tool_calls=[tool_call]))
            elif "observation" in orchestration_trace:
                observation = orchestration_trace["observation"]
                if observation.get("type") == "KNOWLEDGE_BASE":
                    kb_output = observation.get("knowledgeBaseLookupOutput", {})
                    tool_result = json.dumps(kb_output.get("retrievedReferences", []))
                    messages.append(
                        ToolMessage(
                            tool_name="knowledge_base_lookup",
                            tool_call_id=observation.get("traceId", ""),
                            content=[
                                MessageContentText(type="text", text=str(tool_result))
                            ],
                        )
                    )
                elif observation.get("type") == "ACTION_GROUP":
                    action_group_output = observation.get(
                        "actionGroupInvocationOutput", {}
                    )

                    try:
                        tool_result = json.loads(action_group_output.get("text", ""))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        tool_result = action_group_output.get("text", "")
                    messages.append(
                        ToolMessage(
                            tool_name="action_group_invocation",
                            tool_call_id=observation.get("traceId", ""),
                            content=[
                                MessageContentText(type="text", text=str(tool_result))
                            ],
                        )
                    )

        logger.info("Converted Bedrock traces into %d messages", len(messages))
        return messages

    def _prepare_input(self, input_data: List[AgentMessage]) -> str:
        """Extract user message from List[AgentMessage]."""
        logger.debug("Preparing Bedrock input from %d messages", len(input_data))
        last_user_message = input_data[-1]
        if last_user_message.role != "user":
            logger.error("Last message is not from user")
            return ""
        # Check if content list is not empty and has text
        if not last_user_message.content:
            logger.error("User message has no content")
            raise ValueError("User message has no content")
        # Find the first text content item
        for content_item in last_user_message.content:
            if content_item.type == "text" and content_item.text:
                logger.debug(
                    "Prepared Bedrock input (text_length=%d)", len(content_item.text)
                )
                return content_item.text
        raise ValueError("No text content found in user message")

    def _run_agent(self, session_id: str, prompt: str) -> List[Dict]:
        """
        Run the Bedrock agent and collect response and traces.

        Args:
            session_id: Unique session identifier
            prompt: Input prompt for the agent

        Returns:
            List of traces
        """
        try:
            agent_answer = ""
            logger.debug(
                "Invoking Bedrock agent (session_id=%s, prompt_length=%d)",
                session_id,
                len(prompt),
            )
            response = self.bedrock_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=prompt,
                enableTrace=True,
            )

            stream = response["completion"]
            traces = []

            for event in stream:
                if "chunk" in event:
                    data = event["chunk"]["bytes"]
                    agent_answer = data.decode("utf8")
                event_trace = event.get("trace")

                if event_trace:
                    traces.append(event_trace)

        except ClientError:
            logger.exception("Error invoking Bedrock agent via Bedrock runtime")
            return "", []
        logger.info(
            "Bedrock agent invocation succeeded (session_id=%s, trace_events=%d)",
            session_id,
            len(traces),
        )
        return agent_answer, traces

    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Union[str, None],
    ) -> AgentInvocationResponse:
        """Asynchronous invocation method - invokes the Bedrock agent and converts to List[AgentMessage].

        Args:
            input: List of AgentMessage objects
            session_id: Unique session identifier

        Returns:
            AgentInvocationResponse - response containing agent trace, trajectory, and final response.
        """
        logger.info(
            "Bedrock ainvoke called (session_id=%s, input_messages=%d)",
            session_id,
            len(input),
        )
        agent_input = self._prepare_input(input)
        session_id = session_id or str(uuid.uuid4())

        try:
            # Run the synchronous _run_agent in a thread pool to avoid blocking
            _, traces = await asyncio.to_thread(
                self._run_agent, session_id, agent_input
            )
            logger.debug(
                "Bedrock agent run returned %d trace events for session_id=%s",
                len(traces),
                session_id,
            )
        except (ClientError, ValueError, KeyError, json.JSONDecodeError):
            logger.exception("Error invoking Bedrock agent")
            return AgentInvocationResponse()

        try:
            agent_trajectory = self._convert_bedrock_traces_to_messages(traces)
            logger.info(
                "Bedrock agent produced %d trajectory messages",
                len(agent_trajectory),
            )

            return AgentInvocationResponse(
                agent_trajectory=agent_trajectory,
            )

        except (ClientError, ValueError, KeyError, json.JSONDecodeError):
            logger.exception("Error converting Bedrock traces to messages")
            return AgentInvocationResponse()
