"""
Unit tests for database.py database setup and session management.

Tests database session lifecycle and dependency injection.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestGetDb:
    """Tests for get_db dependency function."""

    @pytest.mark.asyncio
    async def test_yields_session(self):
        """Should yield a database session."""
        from app.database import get_db

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        mock_session_maker = MagicMock()
        mock_session_maker.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.__aexit__ = AsyncMock(return_value=None)

        with patch("app.database.async_session_maker", return_value=mock_session_maker):
            gen = get_db()
            session = await gen.__anext__()

            assert session == mock_session

    @pytest.mark.asyncio
    async def test_commits_on_success(self):
        """Should commit session on successful completion."""
        from app.database import get_db

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("app.database.async_session_maker", return_value=mock_context):
            gen = get_db()
            await gen.__anext__()

            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollbacks_on_exception(self):
        """Should rollback session on exception."""
        from app.database import get_db

        mock_session = MagicMock()
        mock_session.commit = AsyncMock(side_effect=Exception("DB error"))
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("app.database.async_session_maker", return_value=mock_context):
            gen = get_db()
            await gen.__anext__()

            with pytest.raises(Exception, match="DB error"):
                await gen.__anext__()

            mock_session.rollback.assert_called_once()


class TestInitDb:
    """Tests for init_db function."""

    @pytest.mark.asyncio
    async def test_creates_all_tables(self):
        """Should create all tables using Base.metadata."""
        from app.database import init_db, Base

        mock_conn = MagicMock()
        mock_conn.run_sync = AsyncMock()

        mock_engine_context = MagicMock()
        mock_engine_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine_context.__aexit__ = AsyncMock(return_value=None)

        with patch("app.database.engine") as mock_engine:
            mock_engine.begin.return_value = mock_engine_context

            await init_db()

            mock_conn.run_sync.assert_called_once()
            # Verify it was called with create_all
            call_args = mock_conn.run_sync.call_args[0][0]
            assert call_args == Base.metadata.create_all
