"""
HTTP Adapter - Connects to remote agent servers via HTTP.

This module provides a BaseAdapter implementation that calls remote agent
servers via HTTP endpoints, enabling distributed agent evaluation.
"""

from typing import Any, Dict, List, Optional, Union

import httpx

from quraite.adapters.base import BaseAdapter
from quraite.logger import get_logger
from quraite.schema.message import AgentMessage
from quraite.schema.response import AgentInvocationResponse

logger = get_logger(__name__)


class HttpAdapter(BaseAdapter):
    """
    HTTP adapter client that communicates with agent servers via HTTP.

    This class implements the BaseAdapter interface and forwards adapter
    requests to a HTTP agent server, handling serialization, network errors,
    and retries.

    Args:
        url: The full URL of the remote agent endpoint (e.g., "http://localhost:8000/v1/agents/completions")
        headers: Optional dictionary of HTTP headers to include in requests
        timeout: Request timeout in seconds (default: 60)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial retry delay in seconds (default: 1)

    Example:
        ```python
        remote_agent = HttpAdapter(
            url="http://localhost:8000/v1/agents/completions",
            headers={"Authorization": "Bearer secret_key"}
        )

        result = remote_agent.ainvoke(
            input=[UserMessage(...)],
            session_id="conv_123"
        )
        ```
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize the HTTP adapter client."""
        self.url = url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Create HTTP client with user-provided headers
        # Always include Content-Type if not provided
        client_headers = {"Content-Type": "application/json"}
        client_headers.update(self.headers)

        self.async_client = httpx.AsyncClient(
            headers=client_headers,
            timeout=self.timeout,
        )
        logger.info(
            "HttpAdapter initialized (url=%s, timeout=%s, max_retries=%s)",
            self.url,
            self.timeout,
            self.max_retries,
        )

    def _serialize_request(
        self,
        input: List[AgentMessage],
        session_id: Union[str, None],
    ) -> Dict[str, Any]:
        """
        Serialize invocation request to JSON-compatible dict.

        Args:
            input: List[AgentMessage] containing user_message
            session_id: Optional conversation ID for maintaining context

        Returns:
            Dictionary ready for JSON serialization
        """
        logger.debug(
            "Serializing HTTP request (messages=%d, session_id=%s)",
            len(input),
            session_id,
        )
        return {
            "input": [msg.model_dump(mode="json") for msg in input],
            "session_id": session_id,
        }

    async def _make_request_with_retry_async(
        self,
        method: str,
        url: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic (asynchronous).

        Args:
            method: HTTP method (POST)
            url: Full URL of the endpoint
            payload: Request payload

        Returns:
            Response data as dictionary
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = await self.async_client.request(
                    method=method,
                    url=url,
                    json=payload,
                )
                response.raise_for_status()
                logger.info(
                    "HTTP request succeeded (status=%s, attempt=%d)",
                    response.status_code,
                    attempt + 1,
                )
                return response.json()

            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                logger.error(
                    "Failed while invoking the url '%s' with status code '%s' and detail '%s'",
                    url,
                    e.response.status_code,
                    error_detail,
                )

                raise e

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                # Retry on network errors
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        "HTTP adapter retrying after network/connection error (retry_in=%.2fs)",
                        delay,
                    )
                    await self._async_sleep(delay)
                else:
                    logger.error(
                        "Failed while connecting to the url %s after %d attempts. Last error: %s",
                        url,
                        self.max_retries,
                        last_exception,
                    )
                    raise last_exception

        logger.error(
            "HTTP adapter failed while invoking the url %s after %d attempts. Last error: %s",
            url,
            self.max_retries,
            last_exception,
        )

        raise last_exception

    @staticmethod
    async def _async_sleep(seconds: float):
        """Helper for async sleep."""
        import asyncio

        await asyncio.sleep(seconds)

    async def ainvoke(
        self,
        input: List[AgentMessage],
        session_id: Union[str, None],
    ) -> AgentInvocationResponse:
        """
        Asynchronously invoke the HTTP agent.

        Args:
            input: List[AgentMessage] containing user_message
            session_id: Optional conversation ID for maintaining context

        Returns:
            AgentInvocationResponse: Response containing agent trace, trajectory, and final response.
        """
        logger.info(
            "HTTP ainvoke called (session_id=%s, input_messages=%d)",
            session_id,
            len(input),
        )
        payload = self._serialize_request(input, session_id)
        response_data = await self._make_request_with_retry_async(
            method="POST", url=self.url, payload=payload
        )
        logger.debug(
            "HTTP adapter received response keys: %s", list(response_data.keys())
        )

        return AgentInvocationResponse.model_validate(
            response_data.get("agent_response", {})
        )

    async def aclose(self):
        """Close async HTTP client."""
        await self.async_client.aclose()
        logger.debug("HTTP adapter client closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()


if __name__ == "__main__":
    import asyncio
    import json

    from quraite.schema.message import MessageContentText, UserMessage

    async def test_http_adapter():
        adapter = HttpAdapter(url="http://localhost:8080/v1/agents/completions")

        try:
            response = await adapter.ainvoke(
                input=[
                    UserMessage(
                        content=[MessageContentText(text="What is 34354 - 54?")]
                    )
                ],
                session_id="test",
            )
            print(response.agent_trajectory)
        except httpx.HTTPStatusError as e:
            print(json.loads(e.response.text)["detail"])
        except Exception as e:
            print(e)

    asyncio.run(test_http_adapter())
