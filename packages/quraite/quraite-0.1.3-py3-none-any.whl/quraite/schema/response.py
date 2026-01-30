from typing import List, Optional

from pydantic import BaseModel

from quraite.schema.message import AgentMessage
from quraite.tracing.trace import AgentTrace


class AgentInvocationResponse(BaseModel):
    """
    Response model for agent invocation.
    """

    agent_trace: Optional[AgentTrace] = None
    agent_trajectory: Optional[List[AgentMessage]] = None
    agent_final_response: Optional[str] = None
