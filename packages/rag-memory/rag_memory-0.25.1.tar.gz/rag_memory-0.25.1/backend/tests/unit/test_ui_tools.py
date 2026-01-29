"""
Unit tests for ui_tools.py UI control tools.

Tests the open_file_upload_dialog tool and its validation logic.
"""

import pytest


class TestOpenFileUploadDialog:
    """Tests for open_file_upload_dialog tool."""

    @pytest.mark.asyncio
    async def test_returns_open_modal_action_for_file_tab(self):
        """File tab should return open_modal action with correct params."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({
            "tab": "file",
            "collection_name": "test-collection",
        })

        assert result["action"] == "open_modal"
        assert result["modal"] == "ingestion"
        assert result["tab"] == "file"
        assert result["params"]["collection_name"] == "test-collection"
        assert "files" in result["message"]

    @pytest.mark.asyncio
    async def test_returns_open_modal_action_for_directory_tab(self):
        """Directory tab should return open_modal action with correct params."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({
            "tab": "directory",
        })

        assert result["action"] == "open_modal"
        assert result["tab"] == "directory"
        assert "directory" in result["message"]

    @pytest.mark.asyncio
    async def test_default_tab_is_file(self):
        """Default tab should be 'file'."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({})

        assert result["tab"] == "file"

    @pytest.mark.asyncio
    async def test_passes_topic_parameter(self):
        """Topic parameter should be included in params."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({
            "topic": "React hooks",
        })

        assert result["params"]["topic"] == "React hooks"

    @pytest.mark.asyncio
    async def test_passes_mode_parameter(self):
        """Mode parameter should be included in params."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({
            "mode": "reingest",
        })

        assert result["params"]["mode"] == "reingest"

    @pytest.mark.asyncio
    async def test_default_mode_is_ingest(self):
        """Default mode should be 'ingest'."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({})

        assert result["params"]["mode"] == "ingest"

    @pytest.mark.asyncio
    async def test_passes_reviewed_by_human_parameter(self):
        """reviewed_by_human parameter should be included in params."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({
            "reviewed_by_human": True,
        })

        assert result["params"]["reviewed_by_human"] is True

    @pytest.mark.asyncio
    async def test_default_reviewed_by_human_is_false(self):
        """Default reviewed_by_human should be False."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({})

        assert result["params"]["reviewed_by_human"] is False

    @pytest.mark.asyncio
    async def test_invalid_tab_returns_error(self):
        """Invalid tab value should return error action."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({
            "tab": "invalid_tab",
        })

        assert result["action"] == "error"
        assert "Invalid tab" in result["error"]

    @pytest.mark.asyncio
    async def test_invalid_mode_returns_error(self):
        """Invalid mode value should return error action."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({
            "mode": "invalid_mode",
        })

        assert result["action"] == "error"
        assert "Invalid mode" in result["error"]

    @pytest.mark.asyncio
    async def test_collection_name_none_by_default(self):
        """collection_name should be None by default."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({})

        assert result["params"]["collection_name"] is None

    @pytest.mark.asyncio
    async def test_topic_none_by_default(self):
        """topic should be None by default."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({})

        assert result["params"]["topic"] is None

    @pytest.mark.asyncio
    async def test_all_parameters_together(self):
        """All parameters should work together."""
        from app.tools.ui_tools import open_file_upload_dialog

        result = await open_file_upload_dialog.ainvoke({
            "tab": "directory",
            "collection_name": "my-docs",
            "topic": "API documentation",
            "mode": "reingest",
            "reviewed_by_human": True,
        })

        assert result["action"] == "open_modal"
        assert result["tab"] == "directory"
        assert result["params"]["collection_name"] == "my-docs"
        assert result["params"]["topic"] == "API documentation"
        assert result["params"]["mode"] == "reingest"
        assert result["params"]["reviewed_by_human"] is True
