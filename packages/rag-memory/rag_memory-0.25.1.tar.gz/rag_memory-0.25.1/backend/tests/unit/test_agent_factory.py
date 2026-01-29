"""
Unit tests for shared/agent_factory.py agent factory functions.

Tests the factory functions that create MCP client and RAG Memory agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestGetMcpClient:
    """Tests for get_mcp_client function."""

    @pytest.mark.asyncio
    async def test_returns_mcp_client(self):
        """Should return MCP client from get_mcp_tools."""
        from app.shared import agent_factory

        mock_client = MagicMock()

        with patch("app.rag_agent.agent.get_mcp_tools", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (mock_client, [MagicMock()])

            client = await agent_factory.get_mcp_client()

        assert client == mock_client

    @pytest.mark.asyncio
    async def test_raises_if_client_is_none(self):
        """Should raise RuntimeError if client creation fails."""
        from app.shared import agent_factory

        with patch("app.rag_agent.agent.get_mcp_tools", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (None, [])

            with pytest.raises(RuntimeError, match="Failed to create MCP client"):
                await agent_factory.get_mcp_client()


class TestCreateRagMemoryAgent:
    """Tests for create_rag_memory_agent function."""

    @pytest.mark.asyncio
    async def test_creates_agent_with_checkpointer(self):
        """Should create agent using checkpointer and create_rag_agent."""
        from app.shared import agent_factory

        mock_checkpointer = MagicMock()
        mock_agent = MagicMock()

        with patch.object(agent_factory, "get_or_create_checkpointer", new_callable=AsyncMock) as mock_cp:
            mock_cp.return_value = mock_checkpointer

            with patch.object(agent_factory, "create_rag_agent", new_callable=AsyncMock) as mock_create:
                mock_create.return_value = mock_agent

                agent = await agent_factory.create_rag_memory_agent()

        assert agent == mock_agent
        mock_cp.assert_called_once()
        mock_create.assert_called_once_with(
            mcp_config_path="mcp.json",
            checkpointer=mock_checkpointer,
        )

    @pytest.mark.asyncio
    async def test_passes_mcp_config_path(self):
        """Should pass mcp.json as config path."""
        from app.shared import agent_factory

        with patch.object(agent_factory, "get_or_create_checkpointer", new_callable=AsyncMock) as mock_cp:
            mock_cp.return_value = MagicMock()

            with patch.object(agent_factory, "create_rag_agent", new_callable=AsyncMock) as mock_create:
                mock_create.return_value = MagicMock()

                await agent_factory.create_rag_memory_agent()

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["mcp_config_path"] == "mcp.json"
