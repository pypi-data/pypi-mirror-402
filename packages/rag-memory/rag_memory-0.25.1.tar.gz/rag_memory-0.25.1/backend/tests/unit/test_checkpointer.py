"""
Unit tests for shared/checkpointer.py AsyncPostgresSaver singleton.

Tests checkpointer creation and connection pool management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestGetOrCreateCheckpointer:
    """Tests for get_or_create_checkpointer function."""

    @pytest.mark.asyncio
    async def test_creates_checkpointer_on_first_call(self):
        """Should create AsyncPostgresSaver on first call."""
        import app.shared.checkpointer as cp_module

        # Reset global state
        cp_module.connection_pool = None
        cp_module.checkpointer = None

        mock_pool = MagicMock()
        mock_pool.open = AsyncMock()
        mock_checkpointer = MagicMock()

        with patch.object(cp_module, "AsyncConnectionPool", return_value=mock_pool):
            with patch.object(cp_module, "AsyncPostgresSaver", return_value=mock_checkpointer):
                result = await cp_module.get_or_create_checkpointer()

        assert result == mock_checkpointer
        mock_pool.open.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_cached_checkpointer(self):
        """Should return cached checkpointer on subsequent calls."""
        import app.shared.checkpointer as cp_module

        # Pre-populate cache
        mock_checkpointer = MagicMock()
        cp_module.checkpointer = mock_checkpointer
        cp_module.connection_pool = MagicMock()

        result = await cp_module.get_or_create_checkpointer()

        assert result == mock_checkpointer

    @pytest.mark.asyncio
    async def test_converts_database_url_format(self):
        """Should convert asyncpg URL format to psycopg format."""
        import app.shared.checkpointer as cp_module

        # Reset global state
        cp_module.connection_pool = None
        cp_module.checkpointer = None

        captured_url = None

        def capture_url(url, **kwargs):
            nonlocal captured_url
            captured_url = url
            mock = MagicMock()
            mock.open = AsyncMock()
            return mock

        with patch.object(cp_module, "AsyncConnectionPool", side_effect=capture_url):
            with patch.object(cp_module, "AsyncPostgresSaver", return_value=MagicMock()):
                await cp_module.get_or_create_checkpointer()

        # URL should NOT contain +asyncpg
        assert "+asyncpg" not in captured_url

    @pytest.mark.asyncio
    async def test_configures_pool_with_autocommit(self):
        """Should configure connection pool with autocommit=True."""
        import app.shared.checkpointer as cp_module

        # Reset global state
        cp_module.connection_pool = None
        cp_module.checkpointer = None

        captured_kwargs = None

        def capture_kwargs(url, **kwargs):
            nonlocal captured_kwargs
            captured_kwargs = kwargs
            mock = MagicMock()
            mock.open = AsyncMock()
            return mock

        with patch.object(cp_module, "AsyncConnectionPool", side_effect=capture_kwargs):
            with patch.object(cp_module, "AsyncPostgresSaver", return_value=MagicMock()):
                await cp_module.get_or_create_checkpointer()

        assert captured_kwargs["kwargs"]["autocommit"] is True
        assert captured_kwargs["open"] is False  # Don't open in constructor

    @pytest.mark.asyncio
    async def test_opens_pool_explicitly(self):
        """Should call pool.open() explicitly after creation."""
        import app.shared.checkpointer as cp_module

        # Reset global state
        cp_module.connection_pool = None
        cp_module.checkpointer = None

        mock_pool = MagicMock()
        mock_pool.open = AsyncMock()

        with patch.object(cp_module, "AsyncConnectionPool", return_value=mock_pool):
            with patch.object(cp_module, "AsyncPostgresSaver", return_value=MagicMock()):
                await cp_module.get_or_create_checkpointer()

        mock_pool.open.assert_called_once()
