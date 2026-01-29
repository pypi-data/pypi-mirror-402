"""
Unit tests for main.py FastAPI application entry point.

Tests app configuration, migrations, and starter prompt seeding.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


class TestRunMigrations:
    """Tests for run_migrations function."""

    def test_runs_alembic_upgrade(self):
        """Should run alembic upgrade head."""
        from app.main import run_migrations

        mock_config_instance = MagicMock()

        with patch("alembic.config.Config", return_value=mock_config_instance):
            with patch("alembic.command.upgrade") as mock_upgrade:
                with patch("psycopg.connect") as mock_psycopg:
                    mock_conn = MagicMock()
                    mock_psycopg.return_value.__enter__ = MagicMock(return_value=mock_conn)
                    mock_psycopg.return_value.__exit__ = MagicMock(return_value=None)

                    with patch("langgraph.checkpoint.postgres.PostgresSaver") as mock_saver:
                        mock_saver_instance = MagicMock()
                        mock_saver.return_value = mock_saver_instance

                        run_migrations()

                        mock_upgrade.assert_called_once()
                        # Verify it upgrades to "head"
                        call_args = mock_upgrade.call_args[0]
                        assert call_args[1] == "head"

    def test_raises_if_alembic_ini_missing(self, tmp_path, monkeypatch):
        """Should raise RuntimeError if alembic.ini not found."""
        from app.main import run_migrations

        # Patch Path(__file__) to point to a directory without alembic.ini
        fake_main_file = tmp_path / "app" / "main.py"
        fake_main_file.parent.mkdir(parents=True, exist_ok=True)
        fake_main_file.touch()

        # Make the backend_dir point to tmp_path (no alembic.ini there)
        with patch("app.main.Path") as mock_path:
            mock_path.return_value.parent.parent = tmp_path

            with pytest.raises(RuntimeError, match="alembic.ini not found"):
                run_migrations()

    def test_sets_up_langgraph_checkpointer(self):
        """Should setup LangGraph checkpointer tables."""
        from app.main import run_migrations

        mock_config_instance = MagicMock()

        with patch("alembic.config.Config", return_value=mock_config_instance):
            with patch("alembic.command.upgrade"):
                with patch("psycopg.connect") as mock_psycopg:
                    mock_conn = MagicMock()
                    mock_psycopg.return_value.__enter__ = MagicMock(return_value=mock_conn)
                    mock_psycopg.return_value.__exit__ = MagicMock(return_value=None)

                    with patch("langgraph.checkpoint.postgres.PostgresSaver") as mock_saver:
                        mock_saver_instance = MagicMock()
                        mock_saver.return_value = mock_saver_instance

                        run_migrations()

                        mock_saver_instance.setup.assert_called_once()


class TestSeedStarterPrompts:
    """Tests for seed_starter_prompts function."""

    @pytest.mark.asyncio
    async def test_seeds_prompts_when_empty(self):
        """Should seed prompts when table is empty."""
        from app.main import seed_starter_prompts

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No existing prompts
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.add = MagicMock()

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("app.database.async_session_maker", return_value=mock_context):
            await seed_starter_prompts()

        # Should have added prompts
        assert mock_session.add.call_count > 0
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_when_prompts_exist(self):
        """Should skip seeding when prompts already exist."""
        from app.main import seed_starter_prompts

        mock_session = MagicMock()
        mock_result = MagicMock()
        # Return existing prompts
        mock_result.scalars.return_value.all.return_value = [MagicMock(), MagicMock()]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.add = MagicMock()

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("app.database.async_session_maker", return_value=mock_context):
            await seed_starter_prompts()

        # Should NOT have added any prompts
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio
    async def test_returns_api_info(self, client):
        """GET / should return API info."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["docs"] == "/docs"


class TestAppConfiguration:
    """Tests for FastAPI app configuration."""

    def test_app_has_cors_middleware(self):
        """App should have CORS middleware configured."""
        from app.main import app

        # Check middleware stack
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    def test_app_includes_rag_router(self):
        """App should include RAG router."""
        from app.main import app

        routes = [r.path for r in app.routes]
        # Check for some expected routes
        assert "/api/health" in routes or any("/api/" in r for r in routes)

    def test_app_includes_mcp_proxy_router(self):
        """App should include MCP proxy router."""
        from app.main import app

        routes = [r.path for r in app.routes]
        # Check for MCP proxy routes
        assert any("/api/rag-memory" in r for r in routes)
