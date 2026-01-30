from enum import Enum

QURAITE_TRACER_NAME = "quraite.instrumentation"


class Framework(str, Enum):
    """Supported agent frameworks."""

    DEFAULT = "default"
    PYDANTIC_AI = "pydantic_ai"
    LANGCHAIN = "langchain"
    GOOGLE_ADK = "google_adk"
    OPENAI_AGENTS = "openai_agents"
    AGNO = "agno"
    SMOLAGENTS = "smolagents"
