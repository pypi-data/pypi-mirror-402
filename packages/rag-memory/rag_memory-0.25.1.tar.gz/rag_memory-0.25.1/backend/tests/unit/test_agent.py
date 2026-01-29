"""
Unit tests for rag_agent/agent.py agent creation and MCP tool loading.

Tests agent creation with mocked external dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestGetMcpTools:
    """Tests for get_mcp_tools function."""

    @pytest.mark.asyncio
    async def test_connects_to_mcp_server(self):
        """Should connect to MCP server and load tools."""
        import app.rag_agent.agent as agent_module

        # Reset global cache
        agent_module._mcp_client = None
        agent_module._mcp_tools = []

        mock_client = MagicMock()
        mock_tools = [MagicMock(name="tool1"), MagicMock(name="tool2")]
        mock_client.get_tools = AsyncMock(return_value=mock_tools)

        with patch.object(agent_module, "MultiServerMCPClient", return_value=mock_client):
            client, tools = await agent_module.get_mcp_tools()

        assert client == mock_client
        assert len(tools) == 2
        mock_client.get_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_caches_client_and_tools(self):
        """Should cache MCP client and tools after first call."""
        import app.rag_agent.agent as agent_module

        # Reset global cache
        agent_module._mcp_client = None
        agent_module._mcp_tools = []

        mock_client = MagicMock()
        mock_tools = [MagicMock()]
        mock_client.get_tools = AsyncMock(return_value=mock_tools)

        with patch.object(agent_module, "MultiServerMCPClient", return_value=mock_client):
            # First call
            await agent_module.get_mcp_tools()
            # Second call should use cache
            client2, tools2 = await agent_module.get_mcp_tools()

        # Should only create client once
        assert client2 == mock_client
        # get_tools called only once due to caching
        assert mock_client.get_tools.call_count == 1

    @pytest.mark.asyncio
    async def test_returns_cached_on_subsequent_calls(self):
        """Subsequent calls should return cached values without reconnecting."""
        import app.rag_agent.agent as agent_module

        # Pre-populate cache
        mock_client = MagicMock()
        mock_tools = [MagicMock(name="cached_tool")]
        agent_module._mcp_client = mock_client
        agent_module._mcp_tools = mock_tools

        client, tools = await agent_module.get_mcp_tools()

        assert client == mock_client
        assert tools == mock_tools


class TestCreateRagAgent:
    """Tests for create_rag_agent function."""

    @pytest.mark.asyncio
    async def test_creates_agent_with_all_tools(self):
        """Should create agent with MCP + Python tools."""
        import app.rag_agent.agent as agent_module

        mock_mcp_tools = [MagicMock(name=f"mcp_tool_{i}") for i in range(17)]
        mock_checkpointer = MagicMock()
        mock_agent = MagicMock()

        with patch.object(agent_module, "get_mcp_tools", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (MagicMock(), mock_mcp_tools)

            with patch.object(agent_module, "create_react_agent", return_value=mock_agent) as mock_create:
                with patch.object(agent_module, "ChatOpenAI"):
                    agent = await agent_module.create_rag_agent(checkpointer=mock_checkpointer)

        assert agent == mock_agent
        mock_create.assert_called_once()

        # Verify all_tools passed to create_react_agent
        call_args = mock_create.call_args
        all_tools = call_args[0][1]  # Second positional arg is tools
        # Should have 17 MCP + 4 Python tools = 21 total
        assert len(all_tools) == 21

    @pytest.mark.asyncio
    async def test_raises_if_no_mcp_tools(self):
        """Should raise RuntimeError if MCP server returns no tools."""
        import app.rag_agent.agent as agent_module

        with patch.object(agent_module, "get_mcp_tools", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (MagicMock(), [])  # No tools

            with pytest.raises(RuntimeError, match="No MCP tools loaded"):
                await agent_module.create_rag_agent()

    @pytest.mark.asyncio
    async def test_configures_llm_with_settings(self):
        """Should configure LLM with settings from config."""
        import app.rag_agent.agent as agent_module

        mock_mcp_tools = [MagicMock()]

        with patch.object(agent_module, "get_mcp_tools", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (MagicMock(), mock_mcp_tools)

            with patch.object(agent_module, "create_react_agent", return_value=MagicMock()):
                with patch.object(agent_module, "ChatOpenAI") as mock_llm:
                    await agent_module.create_rag_agent()

        mock_llm.assert_called_once()
        call_kwargs = mock_llm.call_args[1]
        assert call_kwargs["streaming"] is True

    @pytest.mark.asyncio
    async def test_passes_checkpointer_to_agent(self):
        """Should pass checkpointer to create_react_agent."""
        import app.rag_agent.agent as agent_module

        mock_checkpointer = MagicMock()
        mock_mcp_tools = [MagicMock()]

        with patch.object(agent_module, "get_mcp_tools", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (MagicMock(), mock_mcp_tools)

            with patch.object(agent_module, "create_react_agent", return_value=MagicMock()) as mock_create:
                with patch.object(agent_module, "ChatOpenAI"):
                    await agent_module.create_rag_agent(checkpointer=mock_checkpointer)

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["checkpointer"] == mock_checkpointer

    @pytest.mark.asyncio
    async def test_sets_interrupt_before_tools(self):
        """Should configure agent to interrupt before tool execution."""
        import app.rag_agent.agent as agent_module

        mock_mcp_tools = [MagicMock()]

        with patch.object(agent_module, "get_mcp_tools", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (MagicMock(), mock_mcp_tools)

            with patch.object(agent_module, "create_react_agent", return_value=MagicMock()) as mock_create:
                with patch.object(agent_module, "ChatOpenAI"):
                    await agent_module.create_rag_agent()

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["interrupt_before"] == ["tools"]
