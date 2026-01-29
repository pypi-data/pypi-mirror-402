"""MCP search_documents tool integration tests.

Tests that search_documents() actually finds ingested content via MCP protocol.
This is THE critical test - verifies core RAG functionality works end-to-end.
"""

import json
import pytest
from .conftest import extract_text_content, extract_error_text, extract_result_data

pytestmark = pytest.mark.anyio


class TestSearchDocuments:
    """Test search_documents tool functionality via MCP."""

    async def test_search_finds_ingested_content(self, mcp_session, setup_test_collection):
        """Test that search_documents actually finds ingested content.

        CRITICAL TEST: Verifies core RAG workflow:
        1. Ingest content via MCP
        2. Search for it via MCP
        3. Verify found with correct document ID
        """
        session, transport = mcp_session
        collection = setup_test_collection

        # Step 1: Ingest test content
        test_content = "Python is a high-level programming language with dynamic typing."
        ingest_result = await session.call_tool("ingest_text", {
            "content": test_content,
            "collection_name": collection,
            "document_title": "Python Basics",
            "metadata": json.dumps({"topic": "programming", "level": "beginner"})
        })

        # Verify ingestion succeeded
        assert not ingest_result.isError, f"Ingest failed: {ingest_result}"
        ingest_text = extract_text_content(ingest_result)
        ingest_data = json.loads(ingest_text)
        assert "source_document_id" in ingest_data, "Ingest should return document ID"
        doc_id = ingest_data["source_document_id"]

        # Step 2: Search for the content we just ingested
        search_result = await session.call_tool("search_documents", {
            "query": "Python programming language",
            "collection_name": collection,
            "limit": 10,
            "threshold": 0.5,
            "include_source": False,
            "include_metadata": False
        })

        # Step 3: Verify search actually found it
        assert not search_result.isError, f"Search failed: {search_result}"

        # Extract results using helper (handles structuredContent)
        results = extract_result_data(search_result) or []

        # THE CRITICAL ASSERTION: did we actually find the document?
        assert len(results) > 0, f"Search should return results for ingested content. Got: {results}"

        # Verify result structure and content
        first_result = results[0]
        assert "content" in first_result or "text" in first_result, "Result should have content"
        assert "source_document_id" in first_result, "Result should have source document ID"
        assert first_result["source_document_id"] == doc_id, "Result should match ingested document"

    async def test_search_respects_collection_scope(self, mcp_session, collection_mgr):
        """Test that search respects collection boundaries.

        Ingest into collection A, search collection B, verify not found.
        """
        session, transport = mcp_session

        # Create two separate collections
        collection_a = "test_search_a_" + session._mcp_test_id if hasattr(session, '_mcp_test_id') else "test_search_a"
        collection_b = "test_search_b_" + session._mcp_test_id if hasattr(session, '_mcp_test_id') else "test_search_b"

        await session.call_tool("create_collection", {
            "name": collection_a,
            "description": "Test collection A",
            "domain": "testing",
            "domain_scope": "Test collection A for search isolation testing"
        })
        await session.call_tool("create_collection", {
            "name": collection_b,
            "description": "Test collection B",
            "domain": "testing",
            "domain_scope": "Test collection B for search isolation testing"
        })

        # Ingest into collection A
        await session.call_tool("ingest_text", {
            "content": "Secret content in collection A",
            "collection_name": collection_a,
            "document_title": "Secret Doc"
        })

        # Search collection B (should not find it)
        search_result = await session.call_tool("search_documents", {
            "query": "Secret content",
            "collection_name": collection_b,
            "limit": 10,
            "threshold": 0.3
        })

        assert not search_result.isError, f"Search failed: {search_result}"
        results = extract_result_data(search_result) or []

        # Should not find content from collection A
        assert len(results) == 0, \
            "Should not find content from different collection"
        # Note: Collections persist in test database - this is acceptable for integration tests

    async def test_search_respects_threshold(self, mcp_session, setup_test_collection):
        """Test that search respects similarity threshold.

        Ingest content, search with low and high thresholds.
        """
        session, transport = mcp_session
        collection = setup_test_collection

        # Ingest content
        await session.call_tool("ingest_text", {
            "content": "The quick brown fox jumps over the lazy dog",
            "collection_name": collection,
            "document_title": "Fox Story"
        })

        # Search with loose threshold (should find)
        search_loose = await session.call_tool("search_documents", {
            "query": "fast animal",
            "collection_name": collection,
            "threshold": 0.3,
            "limit": 5
        })

        assert not search_loose.isError
        loose_results = extract_result_data(search_loose) or []

        # Search with tight threshold (may not find if similarity is low)
        search_tight = await session.call_tool("search_documents", {
            "query": "fast animal",
            "collection_name": collection,
            "threshold": 0.95,
            "limit": 5
        })

        assert not search_tight.isError
        tight_results = extract_result_data(search_tight) or []

        # Loose should find at least as many as tight
        assert len(loose_results) >= len(tight_results), "Loose threshold should find at least as many results"

    async def test_search_includes_source_when_requested(self, mcp_session, setup_test_collection):
        """Test that search includes full source document when requested."""
        session, transport = mcp_session
        collection = setup_test_collection

        full_content = "This is a complete document about machine learning and AI concepts."

        # Ingest content
        await session.call_tool("ingest_text", {
            "content": full_content,
            "collection_name": collection,
            "document_title": "ML Guide"
        })

        # Search WITHOUT source
        search_no_source = await session.call_tool("search_documents", {
            "query": "machine learning",
            "collection_name": collection,
            "include_source": False,
            "limit": 1
        })

        no_source_results = extract_result_data(search_no_source) or []

        # Search WITH source
        search_with_source = await session.call_tool("search_documents", {
            "query": "machine learning",
            "collection_name": collection,
            "include_source": True,
            "limit": 1
        })

        with_source_results = extract_result_data(search_with_source) or []

        # With source should include source_content field
        assert len(with_source_results) > 0, "Should find content"
        assert "source_content" in with_source_results[0], "Should include source_content when requested"

    async def test_search_empty_result_for_no_matches(self, mcp_session, setup_test_collection):
        """Test that search returns empty results when nothing matches."""
        session, transport = mcp_session
        collection = setup_test_collection

        # Ingest specific content
        await session.call_tool("ingest_text", {
            "content": "The sky is blue and beautiful",
            "collection_name": collection,
            "document_title": "Sky Description"
        })

        # Search for completely unrelated content
        search_result = await session.call_tool("search_documents", {
            "query": "cryptocurrency bitcoin blockchain ethereum",
            "collection_name": collection,
            "threshold": 0.9,
            "limit": 5
        })

        assert not search_result.isError
        results = json.loads(extract_text_content(search_result)) if extract_text_content(search_result) else []

        # Should return empty or very few results
        assert len(results) == 0 or all(r.get("similarity", 0) < 0.5 for r in results)

    async def test_search_with_metadata_filter(self, mcp_session, setup_test_collection):
        """Test that search respects metadata_filter parameter.

        Ingests multiple documents with different metadata, then searches
        with metadata filters to verify correct filtering behavior.
        """
        session, transport = mcp_session
        collection = setup_test_collection

        # Ingest document with metadata: category=tutorial, level=beginner
        await session.call_tool("ingest_text", {
            "content": "This is a beginner tutorial about Python basics and syntax.",
            "collection_name": collection,
            "document_title": "Python Beginner Tutorial",
            "metadata": json.dumps({"category": "tutorial", "level": "beginner"})
        })

        # Ingest document with metadata: category=tutorial, level=advanced
        await session.call_tool("ingest_text", {
            "content": "This is an advanced tutorial covering Python metaclasses and decorators.",
            "collection_name": collection,
            "document_title": "Python Advanced Tutorial",
            "metadata": json.dumps({"category": "tutorial", "level": "advanced"})
        })

        # Ingest document with metadata: category=reference, level=beginner
        await session.call_tool("ingest_text", {
            "content": "This is a reference guide for Python built-in functions.",
            "collection_name": collection,
            "document_title": "Python Reference",
            "metadata": json.dumps({"category": "reference", "level": "beginner"})
        })

        # Search with filter: only beginner level
        search_beginner = await session.call_tool("search_documents", {
            "query": "Python programming concepts",
            "collection_name": collection,
            "include_metadata": True,
            "metadata_filter": {"level": "beginner"},
            "limit": 10,
            "threshold": 0.3
        })

        assert not search_beginner.isError, f"Search with metadata filter failed: {search_beginner}"
        beginner_results = extract_result_data(search_beginner) or []

        # Verify all results have level=beginner
        assert len(beginner_results) > 0, "Should find beginner content"
        for result in beginner_results:
            metadata = result.get("metadata", {})
            assert metadata.get("level") == "beginner", f"Result should have level=beginner: {metadata}"

        # Search with filter: only tutorial category
        search_tutorial = await session.call_tool("search_documents", {
            "query": "Python programming concepts",
            "collection_name": collection,
            "include_metadata": True,
            "metadata_filter": {"category": "tutorial"},
            "limit": 10,
            "threshold": 0.3
        })

        assert not search_tutorial.isError
        tutorial_results = extract_result_data(search_tutorial) or []

        # Verify all results have category=tutorial
        assert len(tutorial_results) > 0, "Should find tutorial content"
        for result in tutorial_results:
            metadata = result.get("metadata", {})
            assert metadata.get("category") == "tutorial", f"Result should have category=tutorial: {metadata}"

        # Search with multiple filters: category=tutorial AND level=advanced
        search_advanced_tutorial = await session.call_tool("search_documents", {
            "query": "Python programming concepts",
            "collection_name": collection,
            "include_metadata": True,
            "metadata_filter": {"category": "tutorial", "level": "advanced"},
            "limit": 10,
            "threshold": 0.3
        })

        assert not search_advanced_tutorial.isError
        advanced_tutorial_results = extract_result_data(search_advanced_tutorial) or []

        # Verify all results match both filters
        assert len(advanced_tutorial_results) > 0, "Should find advanced tutorial content"
        for result in advanced_tutorial_results:
            metadata = result.get("metadata", {})
            assert metadata.get("category") == "tutorial", "Result should have category=tutorial"
            assert metadata.get("level") == "advanced", "Result should have level=advanced"

        # Search without filter should find all documents
        search_no_filter = await session.call_tool("search_documents", {
            "query": "Python programming concepts",
            "collection_name": collection,
            "include_metadata": True,
            "limit": 10,
            "threshold": 0.3
        })

        assert not search_no_filter.isError
        no_filter_results = extract_result_data(search_no_filter) or []

        # No filter should find more or equal results than with filter
        assert len(no_filter_results) >= len(beginner_results), "No filter should find at least as many results as filtered search"


class TestSearchDocumentsDataFormat:
    """Critical tests to prevent 'NaN% MATCH' bug by verifying data format.

    These tests explicitly verify the contract between MCP tool and chat_bridge.py.
    They ensure search_documents always returns the expected structure:
    - list[dict] (not nested dict)
    - Required fields: content, similarity, source_document_id, source_filename
    - Valid data types (similarity is number, not undefined/NaN)
    """

    async def test_returns_list_of_dicts_with_required_fields(self, mcp_session, setup_test_collection):
        """CRITICAL: Verify search_documents returns list[dict] with all required fields.

        This is the contract expected by chat_bridge.py line 131-145.
        Missing or undefined fields cause 'NaN% MATCH' in frontend.
        """
        session, transport = mcp_session
        collection = setup_test_collection

        # Ingest test content
        await session.call_tool("ingest_text", {
            "content": "TypeScript is a typed superset of JavaScript that compiles to plain JavaScript.",
            "collection_name": collection,
            "document_title": "TypeScript Overview",
            "metadata": json.dumps({"language": "TypeScript", "category": "documentation"})
        })

        # Search for content
        search_result = await session.call_tool("search_documents", {
            "query": "TypeScript JavaScript types",
            "collection_name": collection,
            "limit": 5,
            "threshold": 0.3,
            "include_metadata": False
        })

        assert not search_result.isError, f"Search failed: {search_result}"

        # Extract results
        results = extract_result_data(search_result) or []

        # CRITICAL ASSERTION 1: Must be a list
        assert isinstance(results, list), f"Results must be list[dict], got {type(results)}"
        assert len(results) > 0, "Should find at least one result"

        # CRITICAL ASSERTION 2: Each result must be a dict with ALL required fields
        first_result = results[0]
        assert isinstance(first_result, dict), f"Each result must be dict, got {type(first_result)}"

        required_fields = ["content", "similarity", "source_document_id", "source_filename"]
        for field in required_fields:
            assert field in first_result, f"Missing required field: {field}. Got fields: {list(first_result.keys())}"
            assert first_result[field] is not None, f"Field {field} is None"

        # CRITICAL ASSERTION 3: Similarity must be valid number (not NaN)
        similarity = first_result["similarity"]
        assert isinstance(similarity, (int, float)), f"similarity must be number, got {type(similarity)}"
        assert 0.0 <= similarity <= 1.0, f"similarity must be in [0.0, 1.0], got {similarity}"
        assert similarity == similarity, f"similarity is NaN (NaN != NaN)"

        # CRITICAL ASSERTION 4: Content must be non-empty string
        content = first_result["content"]
        assert isinstance(content, str), f"content must be string, got {type(content)}"
        assert len(content) > 0, "content must not be empty"

        # CRITICAL ASSERTION 5: source_filename must be non-empty string
        source_filename = first_result["source_filename"]
        assert isinstance(source_filename, str), f"source_filename must be string, got {type(source_filename)}"
        assert len(source_filename) > 0, "source_filename must not be empty"

        # CRITICAL ASSERTION 6: source_document_id must be integer
        source_document_id = first_result["source_document_id"]
        assert isinstance(source_document_id, int), f"source_document_id must be int, got {type(source_document_id)}"

    async def test_returns_flat_list_not_nested_dict(self, mcp_session, setup_test_collection):
        """CRITICAL: Verify search_documents returns flat list, not nested dict structure.

        Some bugs occur when API returns {"results": [...]}, but frontend expects [...].
        This test ensures we always get a flat list directly.
        """
        session, transport = mcp_session
        collection = setup_test_collection

        # Ingest test content
        await session.call_tool("ingest_text", {
            "content": "React is a JavaScript library for building user interfaces.",
            "collection_name": collection,
            "document_title": "React Basics"
        })

        # Search for content
        search_result = await session.call_tool("search_documents", {
            "query": "React JavaScript UI library",
            "collection_name": collection,
            "limit": 3
        })

        assert not search_result.isError, f"Search failed: {search_result}"

        # Extract results
        results = extract_result_data(search_result)

        # CRITICAL ASSERTION: Must be a flat list, not nested dict
        assert isinstance(results, list), f"Must return list directly, not dict with 'results' key. Got: {type(results)}"

        # Verify it's not accidentally wrapped
        if isinstance(results, dict):
            # This would be wrong - it should be list, not dict
            assert False, f"Results should be list, not dict with keys: {list(results.keys())}"

        # Verify first item is dict with required fields (not another wrapper)
        if len(results) > 0:
            first = results[0]
            assert isinstance(first, dict), "First result should be dict"
            assert "content" in first, "First result should have 'content' field directly (not nested)"
            assert "similarity" in first, "First result should have 'similarity' field directly"

    async def test_multiple_results_all_have_required_fields(self, mcp_session, setup_test_collection):
        """Verify ALL results have required fields, not just the first one.

        Edge case: Sometimes first result is correct but subsequent results are malformed.
        """
        session, transport = mcp_session
        collection = setup_test_collection

        # Ingest multiple documents
        for i in range(3):
            await session.call_tool("ingest_text", {
                "content": f"Document {i}: This is about programming languages and software development.",
                "collection_name": collection,
                "document_title": f"Programming Doc {i}"
            })

        # Search for content
        search_result = await session.call_tool("search_documents", {
            "query": "programming languages software",
            "collection_name": collection,
            "limit": 10,
            "threshold": 0.3
        })

        assert not search_result.isError
        results = extract_result_data(search_result) or []

        assert len(results) > 1, "Should find multiple results for this test"

        required_fields = ["content", "similarity", "source_document_id", "source_filename"]

        # Verify EVERY result has all required fields
        for idx, result in enumerate(results):
            assert isinstance(result, dict), f"Result {idx} must be dict"

            for field in required_fields:
                assert field in result, f"Result {idx} missing field: {field}"
                assert result[field] is not None, f"Result {idx} has None for field: {field}"

            # Verify similarity is valid for every result
            similarity = result["similarity"]
            assert isinstance(similarity, (int, float)), f"Result {idx} similarity is not number"
            assert 0.0 <= similarity <= 1.0, f"Result {idx} similarity out of range: {similarity}"
            assert similarity == similarity, f"Result {idx} similarity is NaN"
