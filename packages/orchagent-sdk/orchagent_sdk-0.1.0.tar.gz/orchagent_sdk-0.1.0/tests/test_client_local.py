"""
Tests for AgentClient local execution mode.

Tests that the AgentClient correctly:
- Detects local execution mode from environment variables
- Routes calls to local subprocess when in local mode
- Propagates call chain, deadline, and other context via env vars
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

from orchagent.client import (
    AgentClient,
    AgentClientError,
    LocalExecutionError,
    CallChainCycleError,
    TimeoutExceededError,
    LOCAL_EXECUTION_ENV,
    AGENTS_DIR_ENV,
    CALL_CHAIN_ENV,
    DEADLINE_ENV,
    MAX_HOPS_ENV,
    DOWNSTREAM_REMAINING_ENV,
)


class TestLocalModeDetection:
    """Test that AgentClient correctly detects local execution mode."""

    def test_local_mode_off_by_default(self):
        """Without env var, local mode should be off."""
        with patch.dict(os.environ, {}, clear=True):
            # Need service key in non-local mode
            with patch.dict(os.environ, {"ORCHAGENT_SERVICE_KEY": "sk_test_123"}):
                client = AgentClient()
                assert client._local_execution is False

    def test_local_mode_enabled_via_env(self):
        """When ORCHAGENT_LOCAL_EXECUTION=true, local mode should be on."""
        with patch.dict(os.environ, {
            LOCAL_EXECUTION_ENV: "true",
            AGENTS_DIR_ENV: "/tmp/agents",
        }, clear=True):
            client = AgentClient()
            assert client._local_execution is True
            assert client._agents_dir == Path("/tmp/agents")

    def test_service_key_optional_in_local_mode(self):
        """In local mode, service key should not be required."""
        with patch.dict(os.environ, {
            LOCAL_EXECUTION_ENV: "true",
        }, clear=True):
            # Should not raise AgentClientError
            client = AgentClient()
            assert client._local_execution is True
            assert client.service_key is None

    def test_service_key_required_in_http_mode(self):
        """In HTTP mode, service key should be required."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AgentClientError, match="No service key provided"):
                AgentClient()

    def test_call_chain_loaded_from_env_in_local_mode(self):
        """Call chain should be loaded from env var in local mode."""
        with patch.dict(os.environ, {
            LOCAL_EXECUTION_ENV: "true",
            CALL_CHAIN_ENV: "org/agent1@v1,org/agent2@v1",
        }, clear=True):
            client = AgentClient()
            assert client.call_chain == ["org/agent1@v1", "org/agent2@v1"]

    def test_deadline_loaded_from_env_in_local_mode(self):
        """Deadline should be loaded from env var in local mode."""
        with patch.dict(os.environ, {
            LOCAL_EXECUTION_ENV: "true",
            DEADLINE_ENV: "1700000000000",
        }, clear=True):
            client = AgentClient()
            assert client.deadline_ms == 1700000000000

    def test_max_hops_loaded_from_env_in_local_mode(self):
        """Max hops should be loaded from env var in local mode."""
        with patch.dict(os.environ, {
            LOCAL_EXECUTION_ENV: "true",
            MAX_HOPS_ENV: "5",
        }, clear=True):
            client = AgentClient()
            assert client.max_hops == 5


class TestCallRouting:
    """Test that calls are routed correctly based on execution mode."""

    @pytest.mark.asyncio
    async def test_local_mode_routes_to_call_locally(self):
        """In local mode, call() should route to _call_locally()."""
        with patch.dict(os.environ, {
            LOCAL_EXECUTION_ENV: "true",
        }, clear=True):
            client = AgentClient()

            # Mock _call_locally to verify it's called
            client._call_locally = MagicMock(return_value={"result": "local"})

            # Make it awaitable
            async def mock_call_locally(*args, **kwargs):
                return {"result": "local"}
            client._call_locally = mock_call_locally

            result = await client.call("org/agent@v1", {"input": "test"})
            assert result == {"result": "local"}

    @pytest.mark.asyncio
    async def test_http_mode_does_not_route_to_call_locally(self):
        """In HTTP mode, call() should use HTTP, not _call_locally()."""
        with patch.dict(os.environ, {
            "ORCHAGENT_SERVICE_KEY": "sk_test_123",
        }, clear=True):
            client = AgentClient()

            # Mock httpx to avoid actual HTTP calls
            with patch("httpx.AsyncClient") as mock_httpx:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"result": "http"}

                mock_client = MagicMock()
                mock_client.__aenter__ = MagicMock(return_value=mock_client)
                mock_client.__aexit__ = MagicMock(return_value=None)
                mock_client.post = MagicMock(return_value=mock_response)

                # Make async methods awaitable
                async def mock_aenter(*args):
                    return mock_client
                async def mock_aexit(*args):
                    pass
                async def mock_post(*args, **kwargs):
                    return mock_response

                mock_client.__aenter__ = mock_aenter
                mock_client.__aexit__ = mock_aexit
                mock_client.post = mock_post
                mock_httpx.return_value = mock_client

                result = await client.call("org/agent@v1", {"input": "test"})
                assert result == {"result": "http"}


class TestCycleDetection:
    """Test call chain cycle detection."""

    @pytest.mark.asyncio
    async def test_cycle_detected_in_local_mode(self):
        """Cycle detection should work in local mode."""
        with patch.dict(os.environ, {
            LOCAL_EXECUTION_ENV: "true",
            CALL_CHAIN_ENV: "org/agent@v1",
        }, clear=True):
            client = AgentClient()

            with pytest.raises(CallChainCycleError, match="would create a cycle"):
                await client.call("org/agent@v1", {"input": "test"})


class TestCallLocally:
    """Test the _call_locally method directly."""

    @pytest.mark.asyncio
    async def test_agent_not_found_error(self):
        """Should raise LocalExecutionError when agent not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {
                LOCAL_EXECUTION_ENV: "true",
                AGENTS_DIR_ENV: tmpdir,
            }, clear=True):
                client = AgentClient()

                with pytest.raises(LocalExecutionError, match="Agent not found"):
                    await client._call_locally("org/missing@v1", {"input": "test"})

    @pytest.mark.asyncio
    async def test_subprocess_execution(self):
        """Should execute agent via subprocess and return result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock agent structure
            agent_dir = Path(tmpdir) / "testorg" / "testagent"
            bundle_dir = agent_dir / "bundle"
            bundle_dir.mkdir(parents=True)

            # Create agent.json
            (agent_dir / "agent.json").write_text(json.dumps({
                "name": "testagent",
                "version": "v1",
                "entrypoint": "main.py",
            }))

            # Create a simple Python script that echoes input as JSON
            (bundle_dir / "main.py").write_text('''
import sys
import json
input_data = json.loads(sys.stdin.read())
print(json.dumps({"received": input_data["message"]}))
''')

            with patch.dict(os.environ, {
                LOCAL_EXECUTION_ENV: "true",
                AGENTS_DIR_ENV: tmpdir,
            }, clear=True):
                client = AgentClient()

                result = await client._call_locally(
                    "testorg/testagent@v1",
                    {"message": "hello"}
                )

                assert result == {"received": "hello"}

    @pytest.mark.asyncio
    async def test_subprocess_env_propagation(self):
        """Should propagate context via environment variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock agent structure
            agent_dir = Path(tmpdir) / "testorg" / "testagent"
            bundle_dir = agent_dir / "bundle"
            bundle_dir.mkdir(parents=True)

            # Create agent.json
            (agent_dir / "agent.json").write_text(json.dumps({
                "name": "testagent",
                "version": "v1",
                "entrypoint": "main.py",
            }))

            # Create a script that returns env vars
            (bundle_dir / "main.py").write_text('''
import sys
import os
import json
sys.stdin.read()  # consume input
print(json.dumps({
    "local_execution": os.environ.get("ORCHAGENT_LOCAL_EXECUTION"),
    "call_chain": os.environ.get("ORCHAGENT_CALL_CHAIN"),
    "max_hops": os.environ.get("ORCHAGENT_MAX_HOPS"),
}))
''')

            with patch.dict(os.environ, {
                LOCAL_EXECUTION_ENV: "true",
                AGENTS_DIR_ENV: tmpdir,
                MAX_HOPS_ENV: "5",
            }, clear=True):
                client = AgentClient()

                result = await client._call_locally(
                    "testorg/testagent@v1",
                    {"message": "test"}
                )

                assert result["local_execution"] == "true"
                assert "testorg/testagent@v1" in result["call_chain"]
                # Max hops should be decremented by 1
                assert result["max_hops"] == "4"

    @pytest.mark.asyncio
    async def test_subprocess_failure_error(self):
        """Should raise LocalExecutionError on subprocess failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock agent structure
            agent_dir = Path(tmpdir) / "testorg" / "testagent"
            bundle_dir = agent_dir / "bundle"
            bundle_dir.mkdir(parents=True)

            # Create agent.json
            (agent_dir / "agent.json").write_text(json.dumps({
                "name": "testagent",
                "version": "v1",
                "entrypoint": "main.py",
            }))

            # Create a script that exits with error
            (bundle_dir / "main.py").write_text('''
import sys
sys.stdin.read()
print("Error occurred", file=sys.stderr)
sys.exit(1)
''')

            with patch.dict(os.environ, {
                LOCAL_EXECUTION_ENV: "true",
                AGENTS_DIR_ENV: tmpdir,
            }, clear=True):
                client = AgentClient()

                with pytest.raises(LocalExecutionError, match="failed"):
                    await client._call_locally(
                        "testorg/testagent@v1",
                        {"message": "test"}
                    )
