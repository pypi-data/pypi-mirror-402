import asyncio
import os
from contextlib import asynccontextmanager
from typing import List, Literal, Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from quraite.adapters.base import BaseAdapter
from quraite.logger import get_logger
from quraite.schema.message import AgentMessage
from quraite.schema.response import AgentInvocationResponse

logger = get_logger(__name__)


class InvokeRequest(BaseModel):
    """
    Request model for agent invocation endpoints.

    Attributes:
        input: List of AgentMessage objects
        session_id: Optional conversation thread identifier
    """

    input: List[AgentMessage]
    session_id: Optional[str] = None


class InvokeResponse(BaseModel):
    """
    Response model for agent invocation endpoints.

    Attributes:
        agent_response: AgentInvocationResponse object representing agent responses
    """

    agent_response: Optional[AgentInvocationResponse] = None


class LocalAgentServer:
    """
    SDK for creating local agent servers that expose agents via HTTP.

    Usage:
        ```python
        from quraite.serve.local_agent_server import LocalAgentServer
        from quraite.adapters import LangChainAdapter

        sdk = LocalAgentServer(wrapped_agent=LangChainAdapter(agent_graph=agent_graph))
        sdk.start(host="0.0.0.0", port=8000, reload=False)
        ```
    """

    def __init__(
        self,
        wrapped_agent: BaseAdapter = None,
        agent_id: Optional[str] = None,
    ):
        """
        Initialize the Local Agent Server SDK.

        Args:
            wrapped_agent: Optional pre-wrapped local agent instance to register immediately
            agent_id: Optional Quraite platform agent ID. Falls back to QURAITE_AGENT_ID env var.
            quraite_endpoint: Optional Quraite endpoint for updating agent config. Falls back to QURAITE_ENDPOINT env var.
        """

        self._agent = wrapped_agent
        self.public_url = None
        self._tunnel = None
        self.agent_id = agent_id or os.getenv("QURAITE_AGENT_ID")
        self._quraite_endpoint = (
            os.getenv("QURAITE_ENDPOINT") or "https://api.quraite.ai"
        )
        self.agent_url = None
        # Tunnel configuration (set when create_app is called with tunnel params)
        self._tunnel_config = None

        if self._agent is None:
            raise RuntimeError("No local agent provided. Please provide a local agent.")

    def _setup_tunnel_sync(
        self,
        port: int,
        host: str = "0.0.0.0",
        tunnel: Literal["ngrok", "cloudflare"] = "cloudflare",
    ):
        """Synchronous tunnel setup (called from async context)."""
        # Prevent creating multiple tunnels if one already exists
        if self._tunnel is not None:
            return

        if tunnel == "ngrok":
            # TODO: Add debug info if ngrok fails to connect or auth token is not set

            try:
                from pyngrok import ngrok
            except ImportError as e:
                raise ImportError(
                    "Failed to import pyngrok. Please install the 'pyngrok' optional dependency: pip install 'quraite[pyngrok]'"
                ) from e

            try:
                ngrok_tunnel = ngrok.connect(port)
                self.public_url = ngrok_tunnel.public_url
                self._tunnel = ngrok_tunnel
                logger.info("Ngrok tunnel established: %s", self.public_url)
            except Exception as e:
                logger.error(
                    "Failed to create ngrok tunnel: %s. "
                    "Make sure ngrok is installed and authenticated: https://ngrok.com/download",
                    e,
                )
                raise

        elif tunnel == "cloudflare":
            from quraite.serve.cloudflared import connect

            cloudflared_tunnel = connect(
                port, host=host if host != "0.0.0.0" else "localhost"
            )
            self.public_url = cloudflared_tunnel.public_url
            self._tunnel = cloudflared_tunnel
            logger.info("Cloudflare tunnel established: %s", self.public_url)

        self.agent_url = self.public_url

    async def start(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        tunnel: Literal["none", "ngrok", "cloudflare"] = "none",
        **uvicorn_kwargs,
    ):
        """
        Start the local agent server.
        """

        if tunnel == "none":
            self.agent_url = f"http://{host}:{port}"

        app = self.create_app(port=port, host=host, tunnel=tunnel)

        loop = asyncio.get_event_loop()
        if loop.is_running():
            config = uvicorn.Config(app, host=host, port=port, **uvicorn_kwargs)
            server = uvicorn.Server(config)
            await server.serve()
        else:
            uvicorn.run(app, host=host, port=port, **uvicorn_kwargs)

    async def _update_backend_agent_url(self) -> None:
        """
        Update the backend server with the agent URL configuration.

        Makes a PATCH request to /agents/{agent_id}/config/url to update
        the agent's URL in the Quraite platform. Sends the full URL including
        the /v1/agents/completions path.
        """
        if not self.agent_id or not self._quraite_endpoint or not self.agent_url:
            return

        quraite_endpoint = self._quraite_endpoint.rstrip("/")
        endpoint = f"{quraite_endpoint}/agents/{self.agent_id}/config/url"
        # Construct full URL with path
        full_url = f"{self.agent_url.rstrip('/')}/v1/agents/completions"
        payload = {"config": {"url": full_url}}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.patch(endpoint, json=payload)
                response.raise_for_status()
                logger.info("Agent URL registered with Quraite platform: %s", full_url)
        except httpx.HTTPStatusError as e:
            logger.warning(
                "Failed to update agent URL in Quraite platform: HTTP %s - %s. Update manually with URL: %s",
                e.response.status_code,
                e.response.text,
                full_url,
            )
        except httpx.RequestError as e:
            logger.warning(
                "Failed to connect to Quraite backend at %s: %s",
                quraite_endpoint,
                e,
            )
        except Exception as e:
            logger.warning("Unexpected error updating agent URL: %s", e)

    def create_app(
        self,
        port: Optional[int] = None,
        host: str = "0.0.0.0",
        tunnel: Literal["none", "ngrok", "cloudflare"] = "none",
    ) -> FastAPI:
        """
        Create FastAPI app with local agent invocation endpoints.

        Args:
            port: Optional port number (for tunnel setup)
            host: Host address (for tunnel setup)
            tunnel: Tunnel type to use ("none", "ngrok", or "cloudflare")

        Returns:
            FastAPI application instance
        """

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup: Set up tunnel if requested
            if tunnel != "none" and port is not None:
                logger.info("Setting up %s tunnel on port %s...", tunnel, port)
                # Run tunnel setup in thread pool since it's blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, self._setup_tunnel_sync, port, host, tunnel
                )
                # Update backend after tunnel is created
                if self.agent_id and self._quraite_endpoint:
                    await self._update_backend_agent_url()
            elif tunnel == "none" and port is not None:
                self.agent_url = f"http://{host}:{port}"

            logger.info("Local Agent Server started successfully")
            if self.public_url:
                logger.info("Agent publicly available at %s", self.public_url)
                if not self.agent_id or not self._quraite_endpoint:
                    logger.info(
                        "Add this URL to your agent in the Quraite platform: %s",
                        self.agent_url,
                    )
            else:
                logger.info(
                    f"Agent running locally and available at {self.agent_url}/v1/agents/completions. Use a tunnel option to make it publicly available."
                )
            yield

            # Shutdown: Clean up tunnel
            if self._tunnel is not None:
                logger.info("Closing %s tunnel...", tunnel)
                if tunnel == "ngrok":
                    try:
                        from pyngrok import ngrok

                        ngrok.disconnect(self._tunnel.public_url)
                        ngrok.kill()
                        logger.info("Ngrok tunnel closed")
                    except Exception as e:
                        logger.warning("Error closing ngrok tunnel: %s", e)
                elif tunnel == "cloudflare":
                    try:
                        loop = asyncio.get_event_loop()
                        if hasattr(self._tunnel, "disconnect"):
                            await loop.run_in_executor(None, self._tunnel.disconnect)
                        elif hasattr(self._tunnel, "stop"):
                            await loop.run_in_executor(None, self._tunnel.stop)
                        elif hasattr(self._tunnel, "close"):
                            await loop.run_in_executor(None, self._tunnel.close)
                        logger.info("Cloudflare tunnel closed")
                    except Exception as e:
                        logger.warning("Error closing cloudflare tunnel: %s", e)

        app = FastAPI(title="Quraite Local Agent Server", lifespan=lifespan)

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Health check endpoint
        @app.get("/")
        def health_check():
            """Health check endpoint."""
            return {
                "status": "ok",
                "message": "Local Agent Server is running",
                "local_agent_registered": self._agent is not None,
            }

        @app.post(
            "/v1/agents/completions",
            response_model=InvokeResponse,
            tags=["agent_invocation"],
        )
        async def invoke_agent(request: InvokeRequest) -> InvokeResponse:
            """
            Agent invocation endpoint (async by default).

            This endpoint receives an invocation request, deserializes it,
            invokes the registered agent asynchronously, and returns the serialized response.

            Args:
                request: InvokeRequest containing input and parameters

            Returns:
                InvokeResponse with list of serialized messages

            Raises:
                HTTPException 400: If no agent is registered
                HTTPException 422: If request format is invalid
                HTTPException 500: If agent invocation fails

            Example:
                ```python
                POST /v1/agents/completions
                {
                    "input": [{
                        "role": "user",
                        "content": [{
                            "type": "text",
                            "text": "Hello"
                        }]
                    }],
                    "session_id": "session_123",
                }
                ```
            """
            if not self._agent:
                raise HTTPException(
                    status_code=400,
                    detail="No agent registered. Please register an agent before invoking.",
                )

            try:
                # Invoke agent (asynchronously)
                response: AgentInvocationResponse = await self._agent.ainvoke(
                    input=request.input,
                    session_id=request.session_id,
                )

                return InvokeResponse(agent_response=response)

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Agent invocation failed: {str(e)}",
                ) from e

        return app


if __name__ == "__main__":
    import asyncio

    from quraite.adapters.base import DummyAdapter

    server = LocalAgentServer(wrapped_agent=DummyAdapter())
    asyncio.run(
        server.start(host="0.0.0.0", port=8000, reload=False, tunnel="cloudflare")
    )
