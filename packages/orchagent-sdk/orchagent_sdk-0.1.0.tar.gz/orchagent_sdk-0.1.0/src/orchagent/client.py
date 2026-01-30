"""
AgentClient - SDK for agents to call other agents.

Handles:
- Service key authentication
- Call chain propagation (prevents cycles)
- Deadline/timeout propagation
- Downstream cap propagation
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx


# Header names (lowercase for consistency)
CALL_CHAIN_HEADER = "x-orchagent-call-chain"
DEADLINE_HEADER = "x-orchagent-deadline-ms"
MAX_HOPS_HEADER = "x-orchagent-max-hops"
DOWNSTREAM_REMAINING_HEADER = "x-orchagent-downstream-remaining"
REQUEST_ID_HEADER = "x-orchagent-request-id"

# Regex for agent references
_AGENT_REF_RE = re.compile(r"^([a-z0-9][a-z0-9-]*)/([a-z0-9][a-z0-9._-]*)@(v\d+(?:\.\d+){0,2})$")

# Default gateway URL
DEFAULT_GATEWAY_URL = "https://api.orchagent.io"

# Local execution environment variables
LOCAL_EXECUTION_ENV = "ORCHAGENT_LOCAL_EXECUTION"
AGENTS_DIR_ENV = "ORCHAGENT_AGENTS_DIR"
CALL_CHAIN_ENV = "ORCHAGENT_CALL_CHAIN"
DEADLINE_ENV = "ORCHAGENT_DEADLINE_MS"
MAX_HOPS_ENV = "ORCHAGENT_MAX_HOPS"
DOWNSTREAM_REMAINING_ENV = "ORCHAGENT_DOWNSTREAM_REMAINING"

DEFAULT_AGENTS_DIR = Path.home() / ".orchagent" / "agents"


class AgentClientError(Exception):
    """Base exception for AgentClient errors."""

    pass


class DependencyCallError(AgentClientError):
    """Error when calling a dependency agent."""

    def __init__(self, message: str, status_code: int | None = None, response_body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class CallChainCycleError(AgentClientError):
    """Error when a call would create a cycle."""

    pass


class TimeoutExceededError(AgentClientError):
    """Error when the deadline has passed."""

    pass


class LocalExecutionError(AgentClientError):
    """Error during local subprocess execution."""

    def __init__(self, message: str, exit_code: int | None = None, stderr: str | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr


class AgentClient:
    """
    Client for calling other agents from within an orchestrator agent.

    Automatically handles:
    - Service key authentication (from ORCHAGENT_SERVICE_KEY env var)
    - Call chain propagation via X-Orchagent-Call-Chain header
    - Deadline propagation via X-Orchagent-Deadline-Ms header
    - Max hops enforcement

    Usage:
        client = AgentClient()

        # In your agent's endpoint handler:
        async def handle_request(request):
            result = await client.call("joe/leak-finder@v1", {"url": "https://github.com/..."})
            return result

    With FastAPI context:
        from fastapi import Request

        @app.post("/analyze")
        async def analyze(request: Request, input: AnalyzeInput):
            client = AgentClient.from_request(request)
            secrets = await client.call("joe/leak-finder@v1", {"url": input.repo_url})
            return {"secrets": secrets}
    """

    def __init__(
        self,
        service_key: str | None = None,
        gateway_url: str | None = None,
        call_chain: list[str] | None = None,
        deadline_ms: int | None = None,
        max_hops: int | None = None,
        downstream_remaining: int | None = None,
        request_id: str | None = None,
    ):
        """
        Initialize AgentClient.

        Args:
            service_key: Service key for auth. Defaults to ORCHAGENT_SERVICE_KEY env var.
            gateway_url: Gateway URL. Defaults to ORCHAGENT_GATEWAY_URL or api.orchagent.io.
            call_chain: Current call chain (for cycle detection). Usually from request headers.
            deadline_ms: Deadline timestamp in ms. Usually from request headers.
            max_hops: Maximum remaining hops. Usually from request headers.
            downstream_remaining: Remaining downstream cap. Usually from request headers.
            request_id: Request ID for tracing. Usually from request headers.
        """
        # Detect local execution mode
        self._local_execution = os.environ.get(LOCAL_EXECUTION_ENV, "").lower() == "true"
        self._agents_dir = Path(os.environ.get(AGENTS_DIR_ENV, str(DEFAULT_AGENTS_DIR)))

        # Service key - optional in local mode
        self.service_key = service_key or os.environ.get("ORCHAGENT_SERVICE_KEY")
        if not self._local_execution and not self.service_key:
            raise AgentClientError(
                "No service key provided. Set ORCHAGENT_SERVICE_KEY env var or pass service_key parameter."
            )

        self.gateway_url = (
            gateway_url or os.environ.get("ORCHAGENT_GATEWAY_URL") or DEFAULT_GATEWAY_URL
        )

        # Load call chain from env var if in local mode and not provided
        if call_chain is not None:
            self.call_chain = call_chain
        elif self._local_execution:
            chain_str = os.environ.get(CALL_CHAIN_ENV, "")
            self.call_chain = [ref.strip() for ref in chain_str.split(",") if ref.strip()]
        else:
            self.call_chain = []

        # Load deadline from env var if in local mode and not provided
        if deadline_ms is not None:
            self.deadline_ms = deadline_ms
        elif self._local_execution and os.environ.get(DEADLINE_ENV):
            self.deadline_ms = int(os.environ.get(DEADLINE_ENV))  # type: ignore
        else:
            self.deadline_ms = None

        # Load max hops from env var if in local mode and not provided
        if max_hops is not None:
            self.max_hops = max_hops
        elif self._local_execution and os.environ.get(MAX_HOPS_ENV):
            self.max_hops = int(os.environ.get(MAX_HOPS_ENV))  # type: ignore
        else:
            self.max_hops = None

        # Load downstream remaining from env var if in local mode and not provided
        if downstream_remaining is not None:
            self.downstream_remaining = downstream_remaining
        elif self._local_execution and os.environ.get(DOWNSTREAM_REMAINING_ENV):
            self.downstream_remaining = int(os.environ.get(DOWNSTREAM_REMAINING_ENV))  # type: ignore
        else:
            self.downstream_remaining = None

        self.request_id = request_id

    @classmethod
    def from_request(cls, request: Any, service_key: str | None = None) -> "AgentClient":
        """
        Create AgentClient from a FastAPI/Starlette request.

        Automatically extracts call chain and deadline from request headers.

        Args:
            request: FastAPI/Starlette Request object
            service_key: Optional override for service key

        Returns:
            Configured AgentClient instance
        """
        headers = getattr(request, "headers", {})

        # Parse call chain
        chain_header = headers.get(CALL_CHAIN_HEADER, "")
        call_chain = [ref.strip() for ref in chain_header.split(",") if ref.strip()]

        # Parse deadline
        deadline_str = headers.get(DEADLINE_HEADER)
        deadline_ms = int(deadline_str) if deadline_str else None

        # Parse max hops
        max_hops_str = headers.get(MAX_HOPS_HEADER)
        max_hops = int(max_hops_str) if max_hops_str else None

        # Parse downstream remaining
        downstream_str = headers.get(DOWNSTREAM_REMAINING_HEADER)
        downstream_remaining = int(downstream_str) if downstream_str else None

        # Get request ID
        request_id = headers.get(REQUEST_ID_HEADER)

        return cls(
            service_key=service_key,
            call_chain=call_chain,
            deadline_ms=deadline_ms,
            max_hops=max_hops,
            downstream_remaining=downstream_remaining,
            request_id=request_id,
        )

    async def _call_locally(
        self,
        agent_ref: str,
        input_data: dict[str, Any],
        timeout: float | None = None,
    ) -> Any:
        """Execute sub-agent via local subprocess."""
        match = _AGENT_REF_RE.match(agent_ref)
        if not match:
            raise AgentClientError(f"Invalid agent reference: {agent_ref}")

        org, agent, version = match.groups()

        # Find agent directory
        agent_dir = self._agents_dir / org / agent
        meta_path = agent_dir / "agent.json"

        if not meta_path.exists():
            raise LocalExecutionError(
                f"Agent not found: {agent_ref}. "
                f"Download with: orch run {org}/{agent}@{version} --download-only --with-deps"
            )

        with open(meta_path) as f:
            agent_meta = json.load(f)

        # Find entrypoint (check bundle dir first, then agent dir)
        entrypoint = agent_meta.get("entrypoint", "sandbox_main.py")
        bundle_path = agent_dir / "bundle" / entrypoint
        direct_path = agent_dir / entrypoint

        if bundle_path.exists():
            entrypoint_path = bundle_path
            cwd = agent_dir / "bundle"
        elif direct_path.exists():
            entrypoint_path = direct_path
            cwd = agent_dir
        else:
            raise LocalExecutionError(f"Entrypoint not found: {entrypoint}")

        # Build subprocess environment
        env = os.environ.copy()
        env[LOCAL_EXECUTION_ENV] = "true"
        env[AGENTS_DIR_ENV] = str(self._agents_dir)
        env[CALL_CHAIN_ENV] = ",".join(self.call_chain + [agent_ref])

        if self.deadline_ms:
            env[DEADLINE_ENV] = str(self.deadline_ms)
        if self.max_hops is not None:
            env[MAX_HOPS_ENV] = str(max(0, self.max_hops - 1))
        if self.downstream_remaining is not None:
            env[DOWNSTREAM_REMAINING_ENV] = str(self.downstream_remaining)

        # Calculate timeout from deadline
        effective_timeout = timeout or 60.0
        if self.deadline_ms:
            remaining = (self.deadline_ms - int(time.time() * 1000)) / 1000
            if remaining <= 0:
                raise TimeoutExceededError("Deadline passed")
            effective_timeout = min(effective_timeout, remaining)

        # Run subprocess
        try:
            result = subprocess.run(
                ["python3", str(entrypoint_path)],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=str(cwd),
                env=env,
            )
        except subprocess.TimeoutExpired:
            raise TimeoutExceededError(f"Timeout calling {agent_ref}")

        if result.returncode != 0:
            raise LocalExecutionError(
                f"Agent {agent_ref} failed: {result.stderr or result.stdout}",
                exit_code=result.returncode,
                stderr=result.stderr,
            )

        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            raise LocalExecutionError(f"Invalid JSON from {agent_ref}: {result.stdout[:200]}")

    async def call(
        self,
        agent_ref: str,
        input_data: dict[str, Any],
        endpoint: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        """
        Call another agent as a dependency.

        Args:
            agent_ref: Agent reference in format "org/agent@version" (e.g., "joe/leak-finder@v1")
            input_data: Input data to send to the agent
            endpoint: Optional endpoint override (defaults to agent's default_endpoint)
            timeout: Optional timeout override in seconds

        Returns:
            Response data from the agent

        Raises:
            DependencyCallError: If the agent call fails
            CallChainCycleError: If calling this agent would create a cycle
            TimeoutExceededError: If the deadline has passed
        """
        # Validate agent reference
        match = _AGENT_REF_RE.match(agent_ref)
        if not match:
            raise AgentClientError(
                f"Invalid agent reference: {agent_ref}. Must be org/agent@version (e.g., joe/leak-finder@v1)"
            )

        org, agent, version = match.groups()

        # Check for cycles
        if agent_ref in self.call_chain:
            raise CallChainCycleError(
                f"Call to {agent_ref} would create a cycle. Current chain: {' -> '.join(self.call_chain)}"
            )

        # Check deadline
        now_ms = int(time.time() * 1000)
        if self.deadline_ms and now_ms >= self.deadline_ms:
            raise TimeoutExceededError("Deadline has passed, cannot make downstream call")

        # Route based on execution mode
        if self._local_execution:
            return await self._call_locally(agent_ref, input_data, timeout)

        # Calculate remaining time for timeout
        if self.deadline_ms:
            remaining_ms = self.deadline_ms - now_ms
            remaining_seconds = remaining_ms / 1000
            if timeout:
                timeout = min(timeout, remaining_seconds)
            else:
                timeout = remaining_seconds

        # Build URL
        endpoint_path = f"/{endpoint}" if endpoint else ""
        url = f"{self.gateway_url}/{org}/{agent}/{version}{endpoint_path}"

        # Build headers
        headers = {
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }

        # Propagate call chain (append self to chain)
        new_chain = self.call_chain + [agent_ref]
        headers[CALL_CHAIN_HEADER] = ",".join(new_chain)

        # Propagate deadline
        if self.deadline_ms:
            headers[DEADLINE_HEADER] = str(self.deadline_ms)

        # Propagate max hops (decremented)
        if self.max_hops is not None:
            if self.max_hops <= 0:
                raise AgentClientError("Max hops exceeded, cannot make downstream call")
            headers[MAX_HOPS_HEADER] = str(self.max_hops - 1)

        # Propagate downstream remaining
        if self.downstream_remaining is not None:
            headers[DOWNSTREAM_REMAINING_HEADER] = str(self.downstream_remaining)

        # Propagate request ID
        if self.request_id:
            headers[REQUEST_ID_HEADER] = self.request_id

        # Make the call
        try:
            async with httpx.AsyncClient(timeout=timeout or 30.0) as http_client:
                response = await http_client.post(url, json=input_data, headers=headers)

                if response.status_code >= 400:
                    try:
                        error_body = response.json()
                    except Exception:
                        error_body = response.text

                    raise DependencyCallError(
                        f"Agent {agent_ref} returned error: {response.status_code}",
                        status_code=response.status_code,
                        response_body=error_body,
                    )

                return response.json()

        except httpx.TimeoutException as e:
            raise TimeoutExceededError(f"Timeout calling {agent_ref}: {e}") from e
        except httpx.RequestError as e:
            raise DependencyCallError(f"Network error calling {agent_ref}: {e}") from e


# Convenience function for simple cases
async def call_agent(
    agent_ref: str,
    input_data: dict[str, Any],
    service_key: str | None = None,
    **kwargs: Any,
) -> Any:
    """
    Convenience function to call an agent without creating a client instance.

    For most cases, prefer using AgentClient.from_request() for proper
    call chain propagation.

    Args:
        agent_ref: Agent reference in format "org/agent@version"
        input_data: Input data to send
        service_key: Service key (defaults to ORCHAGENT_SERVICE_KEY env var)
        **kwargs: Additional arguments passed to AgentClient.call()

    Returns:
        Response data from the agent
    """
    client = AgentClient(service_key=service_key)
    return await client.call(agent_ref, input_data, **kwargs)
