"""
OrchAgent SDK for agent-to-agent calls.

Usage:
    from orchagent import AgentClient

    client = AgentClient()

    async def my_orchestrator(input):
        result = await client.call("joe/leak-finder@v1", {"url": input["repo"]})
        return result
"""

from .client import (
    AgentClient,
    AgentClientError,
    CallChainCycleError,
    DependencyCallError,
    LocalExecutionError,
    TimeoutExceededError,
    call_agent,
)

__version__ = "0.1.0"

__all__ = [
    "AgentClient",
    "AgentClientError",
    "CallChainCycleError",
    "DependencyCallError",
    "LocalExecutionError",
    "TimeoutExceededError",
    "call_agent",
]
