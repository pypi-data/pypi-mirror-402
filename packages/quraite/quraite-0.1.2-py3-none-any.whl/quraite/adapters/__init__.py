from typing import TYPE_CHECKING

from quraite.adapters.base import BaseAdapter, DummyAdapter
from quraite.adapters.http_adapter import HttpAdapter

if TYPE_CHECKING:
    from quraite.adapters.agno_adapter import AgnoAdapter
    from quraite.adapters.bedrock_agents_adapter import BedrockAgentsAdapter
    from quraite.adapters.flowise_adapter import FlowiseAdapter
    from quraite.adapters.google_adk_adapter import GoogleADKAdapter
    from quraite.adapters.langflow_adapter import LangflowAdapter
    from quraite.adapters.langchain_adapter import LangchainAdapter
    from quraite.adapters.langchain_server_adapter import LangchainServerAdapter
    from quraite.adapters.n8n_adapter import N8nAdapter
    from quraite.adapters.openai_agents_adapter import OpenaiAgentsAdapter
    from quraite.adapters.pydantic_ai_adapter import PydanticAIAdapter
    from quraite.adapters.smolagents_adapter import SmolagentsAdapter


__all__ = [
    "AgnoAdapter",
    "BaseAdapter",
    "BedrockAgentsAdapter",
    "DummyAdapter",
    "FlowiseAdapter",
    "GoogleADKAdapter",
    "LangflowAdapter",
    "LangchainAdapter",
    "LangchainServerAdapter",
    "N8nAdapter",
    "OpenaiAgentsAdapter",
    "PydanticAIAdapter",
    "HttpAdapter",
    "SmolagentsAdapter",
]


def __getattr__(name: str):
    if name == "AgnoAdapter":
        try:
            from quraite.adapters.agno_adapter import AgnoAdapter

            return AgnoAdapter
        except ImportError as e:
            raise ImportError(
                f"Failed to import {name}. Please install the 'agno' optional dependency: pip install 'quraite[agno]'"
            ) from e

    elif name == "BedrockAgentsAdapter":
        try:
            from quraite.adapters.bedrock_agents_adapter import BedrockAgentsAdapter

            return BedrockAgentsAdapter
        except ImportError as e:
            raise ImportError(
                f"Failed to import {name}. Please install the 'bedrock-agents' optional dependency: pip install 'quraite[bedrock-agents]'"
            ) from e

    elif name == "FlowiseAdapter":
        from quraite.adapters.flowise_adapter import FlowiseAdapter

        return FlowiseAdapter

    elif name == "GoogleADKAdapter":
        try:
            from quraite.adapters.google_adk_adapter import GoogleADKAdapter

            return GoogleADKAdapter
        except ImportError as e:
            raise ImportError(
                f"Failed to import {name}. Please install the 'google-adk' optional dependency: pip install 'quraite[google-adk]'"
            ) from e

    elif name == "LangflowAdapter":
        from quraite.adapters.langflow_adapter import LangflowAdapter

        return LangflowAdapter

    elif name == "LangchainAdapter":
        try:
            from quraite.adapters.langchain_adapter import LangchainAdapter

            return LangchainAdapter
        except ImportError as e:
            raise ImportError(
                f"Failed to import {name}. Please install the 'langchain' optional dependency: pip install 'quraite[langchain]'"
            ) from e

    elif name == "LangchainServerAdapter":
        try:
            from quraite.adapters.langchain_server_adapter import LangchainServerAdapter

            return LangchainServerAdapter
        except ImportError as e:
            raise ImportError(
                f"Failed to import {name}. Please install the 'langchain' optional dependency: pip install 'quraite[langchain]'"
            ) from e

    elif name == "N8nAdapter":
        from quraite.adapters.n8n_adapter import N8nAdapter

        return N8nAdapter

    elif name == "OpenaiAgentsAdapter":
        try:
            from quraite.adapters.openai_agents_adapter import OpenaiAgentsAdapter

            return OpenaiAgentsAdapter
        except ImportError as e:
            raise ImportError(
                f"Failed to import {name}. Please install the 'openai-agents' optional dependency: pip install 'quraite[openai-agents]'"
            ) from e

    elif name == "PydanticAIAdapter":
        try:
            from quraite.adapters.pydantic_ai_adapter import PydanticAIAdapter

            return PydanticAIAdapter
        except ImportError as e:
            raise ImportError(
                f"Failed to import {name}. Please install the 'pydantic-ai' optional dependency: pip install 'quraite[pydantic-ai]'"
            ) from e

    elif name == "SmolagentsAdapter":
        try:
            from quraite.adapters.smolagents_adapter import SmolagentsAdapter

            return SmolagentsAdapter
        except ImportError as e:
            raise ImportError(
                f"Failed to import {name}. Please install the 'smolagents' optional dependency: pip install 'quraite[smolagents]'"
            ) from e

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
