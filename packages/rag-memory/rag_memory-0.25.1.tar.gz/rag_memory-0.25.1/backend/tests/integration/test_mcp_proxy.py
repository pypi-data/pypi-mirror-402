"""
Integration tests for mcp_proxy.py MCP proxy endpoints.

Tests all proxy endpoints with mocked MCP tool invocations.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestInvokeMcpTool:
    """Tests for invoke_mcp_tool helper function."""

    @pytest.mark.asyncio
    async def test_parses_json_string_result(self):
        """JSON string results should be parsed to dict."""
        from app.rag.mcp_proxy import invoke_mcp_tool

        mock_tool = MagicMock()
        mock_tool.ainvoke = AsyncMock(return_value='{"key": "value"}')

        with patch("app.rag.mcp_proxy.get_mcp_tool", return_value=mock_tool):
            result = await invoke_mcp_tool("test_tool", {})

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_parses_mcp_content_blocks(self):
        """MCP content block results should have text extracted and parsed."""
        from app.rag.mcp_proxy import invoke_mcp_tool

        mock_tool = MagicMock()
        mock_tool.ainvoke = AsyncMock(return_value=[
            {"type": "text", "text": '{"data": "parsed"}'}
        ])

        with patch("app.rag.mcp_proxy.get_mcp_tool", return_value=mock_tool):
            result = await invoke_mcp_tool("test_tool", {})

        assert result == {"data": "parsed"}

    @pytest.mark.asyncio
    async def test_returns_plain_string_as_is(self):
        """Non-JSON string results should be returned unchanged."""
        from app.rag.mcp_proxy import invoke_mcp_tool

        mock_tool = MagicMock()
        mock_tool.ainvoke = AsyncMock(return_value="plain text result")

        with patch("app.rag.mcp_proxy.get_mcp_tool", return_value=mock_tool):
            result = await invoke_mcp_tool("test_tool", {})

        assert result == "plain text result"

    @pytest.mark.asyncio
    async def test_returns_multi_element_list(self):
        """Multi-element list results should be returned as-is."""
        from app.rag.mcp_proxy import invoke_mcp_tool

        mock_tool = MagicMock()
        mock_tool.ainvoke = AsyncMock(return_value=[
            {"type": "text", "text": '{"a": 1}'},
            {"type": "text", "text": '{"b": 2}'},
        ])

        with patch("app.rag.mcp_proxy.get_mcp_tool", return_value=mock_tool):
            result = await invoke_mcp_tool("test_tool", {})

        # Multi-element list returns list of parsed items
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_handles_non_text_content_blocks(self):
        """Single-element list with plain text returns list (only dicts unwrapped)."""
        from app.rag.mcp_proxy import invoke_mcp_tool

        mock_tool = MagicMock()
        # Single-element list with non-JSON text
        mock_tool.ainvoke = AsyncMock(return_value=[
            {"type": "text", "text": "plain text"}
        ])

        with patch("app.rag.mcp_proxy.get_mcp_tool", return_value=mock_tool):
            result = await invoke_mcp_tool("test_tool", {})

        # The code only unwraps single-element lists if the element is a dict
        # For plain text (string), it returns the list
        assert result == ["plain text"]


class TestGetMcpTool:
    """Tests for get_mcp_tool helper function."""

    @pytest.mark.asyncio
    async def test_caches_tools_on_first_call(self):
        """Tools should be loaded and cached on first call."""
        import app.rag.mcp_proxy as mcp_proxy

        # Reset global cache
        mcp_proxy._mcp_tools_dict = {}

        mock_tool = MagicMock()
        mock_tool.name = "test_tool"

        # Patch at the source module where get_mcp_tools is defined
        with patch("app.rag_agent.agent.get_mcp_tools", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (MagicMock(), [mock_tool])

            result = await mcp_proxy.get_mcp_tool("test_tool")

            assert result == mock_tool
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_for_unknown_tool(self):
        """Unknown tool name should raise ValueError."""
        import app.rag.mcp_proxy as mcp_proxy

        # Reset global cache
        mcp_proxy._mcp_tools_dict = {}

        mock_tool = MagicMock()
        mock_tool.name = "known_tool"

        # Patch at the source module where get_mcp_tools is defined
        with patch("app.rag_agent.agent.get_mcp_tools", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = (MagicMock(), [mock_tool])

            with pytest.raises(ValueError, match="Tool 'unknown_tool' not found"):
                await mcp_proxy.get_mcp_tool("unknown_tool")


class TestCollectionEndpoints:
    """Tests for collection proxy endpoints."""

    @pytest.mark.asyncio
    async def test_list_collections_success(self, client):
        """GET /api/rag-memory/collections should return collections."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = [{"name": "test-collection", "description": "Test"}]

            response = await client.get("/api/rag-memory/collections")

            assert response.status_code == 200
            data = response.json()
            assert "collections" in data
            mock.assert_called_once_with("list_collections", {})

    @pytest.mark.asyncio
    async def test_list_collections_error(self, client):
        """GET /api/rag-memory/collections should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("MCP server unavailable")

            response = await client.get("/api/rag-memory/collections")

            assert response.status_code == 500
            assert "MCP server unavailable" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_collection_info_success(self, client):
        """GET /api/rag-memory/collections/{name} should return collection info."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"name": "test", "document_count": 5}

            response = await client.get("/api/rag-memory/collections/test")

            assert response.status_code == 200
            mock.assert_called_once_with("get_collection_info", {"collection_name": "test"})

    @pytest.mark.asyncio
    async def test_create_collection_success(self, client):
        """POST /api/rag-memory/collections should create collection."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"collection_id": 1, "created": True}

            response = await client.post(
                "/api/rag-memory/collections",
                json={
                    "name": "new-collection",
                    "description": "Test collection",
                    "domain": "testing",
                    "domain_scope": "unit tests",
                },
            )

            assert response.status_code == 200
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_collection_success(self, client):
        """DELETE /api/rag-memory/collections/{name} should delete collection."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"deleted": True}

            response = await client.delete("/api/rag-memory/collections/test")

            assert response.status_code == 200
            mock.assert_called_once_with("delete_collection", {"name": "test", "confirm": True})


class TestDocumentEndpoints:
    """Tests for document proxy endpoints."""

    @pytest.mark.asyncio
    async def test_list_documents_success(self, client):
        """GET /api/rag-memory/documents should return documents."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"documents": [{"id": 1, "filename": "test.md"}]}

            response = await client.get("/api/rag-memory/documents")

            assert response.status_code == 200
            assert "documents" in response.json()

    @pytest.mark.asyncio
    async def test_list_documents_with_params(self, client):
        """GET /api/rag-memory/documents should pass query params."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"documents": []}

            response = await client.get(
                "/api/rag-memory/documents",
                params={"collection_name": "test", "limit": 10, "offset": 5},
            )

            assert response.status_code == 200
            mock.assert_called_once_with("list_documents", {
                "collection_name": "test",
                "limit": 10,
                "offset": 5,
                "include_details": False,
            })

    @pytest.mark.asyncio
    async def test_get_document_success(self, client):
        """GET /api/rag-memory/documents/{id} should return document."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"id": 1, "content": "Test content"}

            response = await client.get("/api/rag-memory/documents/1")

            assert response.status_code == 200
            mock.assert_called_once_with("get_document_by_id", {"document_id": 1})

    @pytest.mark.asyncio
    async def test_delete_document_success(self, client):
        """DELETE /api/rag-memory/documents/{id} should delete document."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"deleted": True}

            response = await client.delete("/api/rag-memory/documents/1")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_document_success(self, client):
        """PATCH /api/rag-memory/documents/{id} should update document."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"updated": True}

            response = await client.patch(
                "/api/rag-memory/documents/1",
                json={"title": "New Title"},
            )

            assert response.status_code == 200


class TestSearchEndpoints:
    """Tests for search proxy endpoints."""

    @pytest.mark.asyncio
    async def test_search_documents_success(self, client):
        """POST /api/rag-memory/search should return search results."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = [{"similarity": 0.9, "content": "Test"}]

            response = await client.post(
                "/api/rag-memory/search",
                json={"query": "test query"},
            )

            assert response.status_code == 200
            assert "results" in response.json()

    @pytest.mark.asyncio
    async def test_search_documents_with_filters(self, client):
        """POST /api/rag-memory/search should pass all parameters."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = []

            response = await client.post(
                "/api/rag-memory/search",
                json={
                    "query": "test",
                    "collection_name": "docs",
                    "limit": 10,
                    "threshold": 0.5,
                    "min_quality_score": 0.7,
                },
            )

            assert response.status_code == 200


class TestGraphEndpoints:
    """Tests for knowledge graph proxy endpoints."""

    @pytest.mark.asyncio
    async def test_query_relationships_success(self, client):
        """POST /api/rag-memory/graph/relationships should return relationships."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"relationships": [{"source": "A", "target": "B"}]}

            response = await client.post(
                "/api/rag-memory/graph/relationships",
                json={"query": "how does X relate to Y?"},
            )

            assert response.status_code == 200
            assert "relationships" in response.json()

    @pytest.mark.asyncio
    async def test_query_relationships_with_collection(self, client):
        """POST /api/rag-memory/graph/relationships should filter by collection."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"relationships": []}

            response = await client.post(
                "/api/rag-memory/graph/relationships",
                json={"query": "test", "collection_name": "docs"},
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_query_temporal_success(self, client):
        """POST /api/rag-memory/graph/temporal should return timeline."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"timeline": [{"fact": "X", "valid_from": "2024-01-01"}]}

            response = await client.post(
                "/api/rag-memory/graph/temporal",
                json={"query": "how has X evolved?"},
            )

            assert response.status_code == 200
            assert "timeline" in response.json()


class TestIngestionEndpoints:
    """Tests for ingestion proxy endpoints."""

    @pytest.mark.asyncio
    async def test_ingest_text_success(self, client):
        """POST /api/rag-memory/ingest/text should ingest text."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"source_document_id": 1, "num_chunks": 3}

            response = await client.post(
                "/api/rag-memory/ingest/text",
                json={
                    "content": "Test content to ingest",
                    "collection_name": "test-collection",
                },
            )

            assert response.status_code == 200
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_text_with_all_params(self, client):
        """POST /api/rag-memory/ingest/text should pass all parameters."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"source_document_id": 1}

            response = await client.post(
                "/api/rag-memory/ingest/text",
                json={
                    "content": "Test",
                    "collection_name": "test",
                    "document_title": "My Doc",
                    "topic": "testing",
                    "reviewed_by_human": True,
                    "mode": "reingest",
                },
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ingest_url_success(self, client):
        """POST /api/rag-memory/ingest/url should ingest URL."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"pages_ingested": 1}

            response = await client.post(
                "/api/rag-memory/ingest/url",
                json={
                    "url": "https://example.com/docs",
                    "collection_name": "test",
                },
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ingest_directory_success(self, client):
        """POST /api/rag-memory/ingest/directory should ingest directory."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"files_ingested": 5}

            response = await client.post(
                "/api/rag-memory/ingest/directory",
                json={
                    "directory_path": "/path/to/docs",
                    "collection_name": "test",
                },
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_analyze_website_success(self, client):
        """POST /api/rag-memory/analyze-website should analyze website."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"total_urls": 50, "pattern_stats": {}}

            response = await client.post(
                "/api/rag-memory/analyze-website",
                json={"base_url": "https://docs.example.com"},
            )

            assert response.status_code == 200


class TestMetadataEndpoints:
    """Tests for metadata proxy endpoints."""

    @pytest.mark.asyncio
    async def test_update_collection_metadata_success(self, client):
        """PATCH /api/rag-memory/collections/{name}/metadata should update metadata."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"fields_added": 2}

            response = await client.patch(
                "/api/rag-memory/collections/test/metadata",
                json={"new_fields": {"custom_field": {"type": "string"}}},
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_collection_schema_success(self, client):
        """GET /api/rag-memory/collections/{name}/schema should return schema."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"metadata_schema": {}}

            response = await client.get("/api/rag-memory/collections/test/schema")

            assert response.status_code == 200


class TestUtilityEndpoints:
    """Tests for utility proxy endpoints."""

    @pytest.mark.asyncio
    async def test_list_directory_success(self, client):
        """POST /api/rag-memory/list-directory should list directory."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.return_value = {"files": [{"path": "/test/file.md"}]}

            response = await client.post(
                "/api/rag-memory/list-directory",
                json={"directory_path": "/test"},
            )

            assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling across endpoints."""

    @pytest.mark.asyncio
    async def test_get_document_error(self, client):
        """GET /api/rag-memory/documents/{id} should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Document not found")

            response = await client.get("/api/rag-memory/documents/999")

            assert response.status_code == 500
            assert "Document not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_document_error(self, client):
        """DELETE /api/rag-memory/documents/{id} should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Cannot delete")

            response = await client.delete("/api/rag-memory/documents/1")

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_search_error(self, client):
        """POST /api/rag-memory/search should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Search failed")

            response = await client.post(
                "/api/rag-memory/search",
                json={"query": "test"},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_query_relationships_error(self, client):
        """POST /api/rag-memory/graph/relationships should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Graph unavailable")

            response = await client.post(
                "/api/rag-memory/graph/relationships",
                json={"query": "test"},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_query_temporal_error(self, client):
        """POST /api/rag-memory/graph/temporal should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Temporal query failed")

            response = await client.post(
                "/api/rag-memory/graph/temporal",
                json={"query": "test"},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_ingest_text_error(self, client):
        """POST /api/rag-memory/ingest/text should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Ingestion failed")

            response = await client.post(
                "/api/rag-memory/ingest/text",
                json={"content": "Test", "collection_name": "test"},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_ingest_url_error(self, client):
        """POST /api/rag-memory/ingest/url should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("URL unreachable")

            response = await client.post(
                "/api/rag-memory/ingest/url",
                json={"url": "https://bad.url", "collection_name": "test"},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_update_document_error(self, client):
        """PATCH /api/rag-memory/documents/{id} should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Update failed")

            response = await client.patch(
                "/api/rag-memory/documents/1",
                json={"title": "New"},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_create_collection_error(self, client):
        """POST /api/rag-memory/collections should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Collection exists")

            response = await client.post(
                "/api/rag-memory/collections",
                json={
                    "name": "existing",
                    "description": "Test",
                    "domain": "test",
                    "domain_scope": "test",
                },
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_delete_collection_error(self, client):
        """DELETE /api/rag-memory/collections/{name} should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Cannot delete")

            response = await client.delete("/api/rag-memory/collections/test")

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_collection_info_error(self, client):
        """GET /api/rag-memory/collections/{name} should return 500 on error."""
        with patch("app.rag.mcp_proxy.invoke_mcp_tool", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Not found")

            response = await client.get("/api/rag-memory/collections/nonexistent")

            assert response.status_code == 500


class TestInvokeMcpToolEdgeCases:
    """Additional edge case tests for invoke_mcp_tool."""

    @pytest.mark.asyncio
    async def test_handles_dict_result(self):
        """Direct dict results should be returned unchanged."""
        from app.rag.mcp_proxy import invoke_mcp_tool

        mock_tool = MagicMock()
        mock_tool.ainvoke = AsyncMock(return_value={"key": "value"})

        with patch("app.rag.mcp_proxy.get_mcp_tool", return_value=mock_tool):
            result = await invoke_mcp_tool("test_tool", {"param": "value"})

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_handles_non_dict_non_list_non_str(self):
        """Other types (int, etc) should be returned as-is."""
        from app.rag.mcp_proxy import invoke_mcp_tool

        mock_tool = MagicMock()
        mock_tool.ainvoke = AsyncMock(return_value=42)

        with patch("app.rag.mcp_proxy.get_mcp_tool", return_value=mock_tool):
            result = await invoke_mcp_tool("test_tool", {})

        assert result == 42

    @pytest.mark.asyncio
    async def test_handles_list_with_non_dict_items(self):
        """List with non-dict items returns parsed list."""
        from app.rag.mcp_proxy import invoke_mcp_tool

        mock_tool = MagicMock()
        mock_tool.ainvoke = AsyncMock(return_value=["item1", "item2"])

        with patch("app.rag.mcp_proxy.get_mcp_tool", return_value=mock_tool):
            result = await invoke_mcp_tool("test_tool", {})

        assert result == ["item1", "item2"]
