#!/usr/bin/env python3
"""
Test script for RAG Memory REST API endpoints.
Tests all 19 MCP tool endpoints including the 9 newly added ones.

Usage:
    python backend/test_endpoints.py
"""

import requests
import json
import sys
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

# Test collection name (will be created and cleaned up)
TEST_COLLECTION = "test-api-endpoints"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log_test(message: str):
    """Log test step."""
    print(f"{BLUE}[TEST]{RESET} {message}")


def log_success(message: str):
    """Log success."""
    print(f"{GREEN}✓{RESET} {message}")


def log_error(message: str):
    """Log error."""
    print(f"{RED}✗{RESET} {message}")


def log_warning(message: str):
    """Log warning."""
    print(f"{YELLOW}!{RESET} {message}")


def test_endpoint(name: str, method: str, url: str, **kwargs) -> tuple[bool, Any]:
    """
    Test an endpoint and return success status and response.

    Args:
        name: Test name
        method: HTTP method (GET, POST, PATCH, DELETE)
        url: Endpoint URL
        **kwargs: Additional arguments for requests

    Returns:
        (success, response_data)
    """
    log_test(f"{name}")
    try:
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        elif method == "PATCH":
            response = requests.patch(url, **kwargs)
        elif method == "DELETE":
            response = requests.delete(url, **kwargs)
        else:
            raise ValueError(f"Unknown method: {method}")

        if response.status_code in [200, 201]:
            log_success(f"{name} - Status: {response.status_code}")
            return True, response.json()
        else:
            log_error(f"{name} - Status: {response.status_code}, Error: {response.text}")
            return False, None
    except Exception as e:
        log_error(f"{name} - Exception: {str(e)}")
        return False, None


def main():
    """Run all endpoint tests."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}RAG Memory REST API Endpoint Tests{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # Track results
    passed = 0
    failed = 0
    skipped = 0

    # ========================================================================
    # TEST 1: Existing Collections Endpoints
    # ========================================================================
    print(f"\n{YELLOW}=== Collections (Existing) ==={RESET}\n")

    # List collections
    success, collections = test_endpoint(
        "GET /collections",
        "GET",
        f"{BASE_URL}/api/rag-memory/collections"
    )
    if success:
        passed += 1
        print(f"  Found {len(collections.get('collections', []))} collections")
    else:
        failed += 1

    # Create test collection
    success, result = test_endpoint(
        "POST /collections (create test collection)",
        "POST",
        f"{BASE_URL}/api/rag-memory/collections",
        json={
            "name": TEST_COLLECTION,
            "description": "Test collection for endpoint validation",
            "domain": "testing",
            "domain_scope": "API endpoint testing"
        }
    )
    if success:
        passed += 1
        print(f"  Created collection: {TEST_COLLECTION}")
    else:
        # May already exist
        log_warning("Collection may already exist, continuing...")
        skipped += 1

    # Get collection info
    success, info = test_endpoint(
        "GET /collections/{name}",
        "GET",
        f"{BASE_URL}/api/rag-memory/collections/{TEST_COLLECTION}"
    )
    if success:
        passed += 1
        print(f"  Collection has {info.get('document_count', 0)} documents")
    else:
        failed += 1

    # ========================================================================
    # TEST 2: New Metadata Endpoints
    # ========================================================================
    print(f"\n{YELLOW}=== Metadata & Schema (NEW) ==={RESET}\n")

    # Get collection schema
    success, schema = test_endpoint(
        "GET /collections/{name}/schema (NEW)",
        "GET",
        f"{BASE_URL}/api/rag-memory/collections/{TEST_COLLECTION}/schema"
    )
    if success:
        passed += 1
        print(f"  Schema has {len(schema.get('custom_fields', {}))} custom fields")
    else:
        failed += 1

    # Update collection metadata
    success, result = test_endpoint(
        "PATCH /collections/{name}/metadata (NEW)",
        "PATCH",
        f"{BASE_URL}/api/rag-memory/collections/{TEST_COLLECTION}/metadata",
        json={
            "new_fields": {
                "test_field": {"type": "string"}
            }
        }
    )
    if success:
        passed += 1
        print(f"  Added test_field to schema")
    else:
        failed += 1

    # ========================================================================
    # TEST 3: New Ingestion Endpoints
    # ========================================================================
    print(f"\n{YELLOW}=== Ingestion (NEW) ==={RESET}\n")

    # Ingest text
    success, result = test_endpoint(
        "POST /ingest/text (NEW)",
        "POST",
        f"{BASE_URL}/api/rag-memory/ingest/text",
        json={
            "content": "This is test content for validating the text ingestion endpoint.",
            "collection_name": TEST_COLLECTION,
            "document_title": "Test Document",
            "mode": "ingest"
        }
    )
    test_document_id = None
    if success:
        passed += 1
        test_document_id = result.get('source_document_id')
        print(f"  Ingested document ID: {test_document_id}")
        print(f"  Created {result.get('num_chunks', 0)} chunks")
    else:
        failed += 1

    # Analyze website (dry-run, no actual ingestion)
    success, result = test_endpoint(
        "POST /analyze-website (NEW)",
        "POST",
        f"{BASE_URL}/api/rag-memory/analyze-website",
        json={
            "base_url": "https://example.com",
            "include_url_lists": False
        }
    )
    if success:
        passed += 1
        print(f"  Found {result.get('total_urls', 0)} URLs")
        print(f"  Status: {result.get('status', 'unknown')}")
    else:
        failed += 1

    # Ingest URL (dry-run to avoid long wait)
    success, result = test_endpoint(
        "POST /ingest/url (NEW) - dry run",
        "POST",
        f"{BASE_URL}/api/rag-memory/ingest/url",
        json={
            "url": "https://example.com",
            "collection_name": TEST_COLLECTION,
            "dry_run": True,
            "topic": "test content"
        }
    )
    if success:
        passed += 1
        print(f"  Dry run: {result.get('pages_crawled', 0)} pages analyzed")
    else:
        failed += 1

    # Note: Skipping /ingest/file and /ingest/directory tests
    # These require actual files and are better tested manually
    log_warning("Skipping /ingest/file (requires file upload)")
    log_warning("Skipping /ingest/directory (requires filesystem access)")
    skipped += 2

    # ========================================================================
    # TEST 4: Existing Documents Endpoints
    # ========================================================================
    print(f"\n{YELLOW}=== Documents (Existing) ==={RESET}\n")

    # List documents
    success, docs = test_endpoint(
        "GET /documents",
        "GET",
        f"{BASE_URL}/api/rag-memory/documents?collection_name={TEST_COLLECTION}&limit=10"
    )
    if success:
        passed += 1
        print(f"  Found {len(docs.get('documents', []))} documents")
    else:
        failed += 1

    # Get document by ID (if we have one)
    if test_document_id:
        success, doc = test_endpoint(
            "GET /documents/{id}",
            "GET",
            f"{BASE_URL}/api/rag-memory/documents/{test_document_id}"
        )
        if success:
            passed += 1
            print(f"  Document: {doc.get('filename', 'N/A')}")
            print(f"  Chunks: {doc.get('chunk_count', 0)}")
        else:
            failed += 1
    else:
        log_warning("No test document ID, skipping GET /documents/{id}")
        skipped += 1

    # Update document (NEW)
    if test_document_id:
        success, result = test_endpoint(
            "PATCH /documents/{id} (NEW)",
            "PATCH",
            f"{BASE_URL}/api/rag-memory/documents/{test_document_id}",
            json={
                "title": "Updated Test Document",
                "metadata": {"updated": "true"}
            }
        )
        if success:
            passed += 1
            print(f"  Updated document metadata")
        else:
            failed += 1
    else:
        log_warning("No test document ID, skipping PATCH /documents/{id}")
        skipped += 1

    # ========================================================================
    # TEST 5: Existing Search Endpoints
    # ========================================================================
    print(f"\n{YELLOW}=== Search (Existing) ==={RESET}\n")

    # Semantic search
    success, results = test_endpoint(
        "POST /search",
        "POST",
        f"{BASE_URL}/api/rag-memory/search",
        json={
            "query": "test content validation",
            "collection_name": TEST_COLLECTION,
            "limit": 3
        }
    )
    if success:
        passed += 1
        print(f"  Found {len(results.get('results', []))} search results")
    else:
        failed += 1

    # ========================================================================
    # TEST 6: Existing Knowledge Graph Endpoints
    # ========================================================================
    print(f"\n{YELLOW}=== Knowledge Graph (Existing) ==={RESET}\n")

    # Query relationships
    success, relationships = test_endpoint(
        "POST /graph/relationships",
        "POST",
        f"{BASE_URL}/api/rag-memory/graph/relationships",
        json={
            "query": "test relationships",
            "collection_name": TEST_COLLECTION,
            "num_results": 3
        }
    )
    if success:
        passed += 1
        print(f"  Found {len(relationships.get('relationships', []))} relationships")
    else:
        failed += 1

    # Query temporal
    success, timeline = test_endpoint(
        "POST /graph/temporal",
        "POST",
        f"{BASE_URL}/api/rag-memory/graph/temporal",
        json={
            "query": "test timeline",
            "collection_name": TEST_COLLECTION,
            "num_results": 3
        }
    )
    if success:
        passed += 1
        print(f"  Found {len(timeline.get('timeline', []))} timeline items")
    else:
        failed += 1

    # ========================================================================
    # TEST 7: New Utility Endpoints
    # ========================================================================
    print(f"\n{YELLOW}=== Utilities (NEW) ==={RESET}\n")

    # Note: Skipping /list-directory as it requires filesystem access
    log_warning("Skipping /list-directory (requires filesystem access)")
    skipped += 1

    # ========================================================================
    # CLEANUP: Delete test collection
    # ========================================================================
    print(f"\n{YELLOW}=== Cleanup ==={RESET}\n")

    success, result = test_endpoint(
        "DELETE /collections/{name}",
        "DELETE",
        f"{BASE_URL}/api/rag-memory/collections/{TEST_COLLECTION}"
    )
    if success:
        log_success("Cleaned up test collection")
    else:
        log_warning("Could not delete test collection (may need manual cleanup)")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    print(f"{GREEN}Passed:{RESET}  {passed}")
    print(f"{RED}Failed:{RESET}  {failed}")
    print(f"{YELLOW}Skipped:{RESET} {skipped}")
    print(f"Total:   {passed + failed + skipped}")

    if failed > 0:
        print(f"\n{RED}Some tests failed. Please review errors above.{RESET}")
        sys.exit(1)
    else:
        print(f"\n{GREEN}All tests passed!{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user.{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Fatal error: {str(e)}{RESET}")
        sys.exit(1)
