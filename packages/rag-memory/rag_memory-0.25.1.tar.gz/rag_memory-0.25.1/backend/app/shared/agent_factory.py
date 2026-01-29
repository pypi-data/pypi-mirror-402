"""Agent factory for creating RAG Memory agent.

Following Lumentor pattern from agent_factory.py (lines 79-90).
"""

import logging

from .checkpointer import get_or_create_checkpointer
from ..rag_agent.agent import create_rag_agent

logger = logging.getLogger(__name__)


async def get_mcp_client():
    """
    Get or create MCP client for direct tool calls.

    Returns:
        MultiServerMCPClient instance
    """
    from ..rag_agent.agent import get_mcp_tools

    logger.info("Getting MCP client...")
    client, _ = await get_mcp_tools(mcp_config_path="mcp.json")

    if not client:
        raise RuntimeError("Failed to create MCP client")

    return client


async def create_rag_memory_agent():
    """
    Create RAG Memory agent with checkpointer.

    Following Lumentor Link Scout pattern exactly.

    Returns:
        Compiled LangGraph agent with PostgresSaver checkpointing
    """
    logger.info("Creating RAG Memory agent instance...")

    # Get PostgresSaver checkpointer
    checkpointer = await get_or_create_checkpointer()
    logger.info("Checkpointer ready")

    # Create agent with MCP + Python tools
    agent = await create_rag_agent(
        mcp_config_path="mcp.json",
        checkpointer=checkpointer,
    )

    logger.info("RAG Memory agent instance created successfully")
    return agent
