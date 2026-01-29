"""MCP Proxy router - proxies RAG Memory requests to MCP server."""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/rag-memory", tags=["mcp-proxy"])
logger = logging.getLogger(__name__)

# Global MCP tools cache
_mcp_tools_dict = {}


async def get_mcp_tool(tool_name: str):
    """Get MCP tool by name, loading and caching tools on first call."""
    global _mcp_tools_dict

    if not _mcp_tools_dict:
        from ..rag_agent.agent import get_mcp_tools

        logger.info("Loading MCP tools for first time...")
        _, tools_list = await get_mcp_tools(mcp_config_path="mcp.json")

        # Convert list to dict for faster lookup
        _mcp_tools_dict = {tool.name: tool for tool in tools_list}
        logger.info(f"Cached {len(_mcp_tools_dict)} MCP tools")

    tool = _mcp_tools_dict.get(tool_name)
    if not tool:
        raise ValueError(f"Tool '{tool_name}' not found")

    return tool


async def invoke_mcp_tool(tool_name: str, params: Dict[str, Any]) -> Any:
    """Invoke an MCP tool and return the result."""
    import json as json_lib

    tool = await get_mcp_tool(tool_name)
    result = await tool.ainvoke(params)

    # Helper to parse MCP content blocks
    def parse_content_block(item):
        """Parse MCP content block {"type": "text", "text": "..."} or JSON string."""
        if isinstance(item, str):
            try:
                return json_lib.loads(item)
            except:
                return item
        elif isinstance(item, dict):
            # MCP content block format: {"type": "text", "text": "..."}
            if item.get("type") == "text" and "text" in item:
                try:
                    return json_lib.loads(item["text"])
                except:
                    return item["text"]
            return item
        return item

    # MCP tools return JSON strings or content blocks
    if isinstance(result, str):
        try:
            return json_lib.loads(result)
        except:
            return result
    elif isinstance(result, list):
        # langchain-mcp-adapters returns results as list of content blocks
        parsed = [parse_content_block(item) for item in result]
        # If single-element list with a dict, return just the dict
        # This handles MCP tools that return dict responses (most tools)
        if len(parsed) == 1 and isinstance(parsed[0], dict):
            return parsed[0]
        return parsed
    else:
        return result


# Request/Response models
class CollectionCreate(BaseModel):
    name: str
    description: str
    domain: str
    domain_scope: str


class SearchRequest(BaseModel):
    query: str
    collection_name: Optional[str] = None
    limit: int = 5
    threshold: float = 0.35
    include_source: bool = False
    include_metadata: bool = False
    metadata_filter: Optional[dict] = None
    # Evaluation filters (all optional, default returns all)
    reviewed_by_human: Optional[bool] = None
    min_quality_score: Optional[float] = None
    min_topic_relevance: Optional[float] = None


class RelationshipRequest(BaseModel):
    query: str
    collection_name: Optional[str] = None
    num_results: int = 5
    threshold: float = 0.2  # Lower default for better recall


# Ingestion request models
class IngestTextRequest(BaseModel):
    content: str
    collection_name: str
    document_title: Optional[str] = None
    metadata: Optional[dict] = None
    include_chunk_ids: bool = False
    mode: str = "ingest"
    # Evaluation parameters
    topic: Optional[str] = None
    reviewed_by_human: bool = False
    # Audit parameters (frontend should use "api" since it's programmatic)
    actor_type: str = "api"


class IngestUrlRequest(BaseModel):
    url: str
    collection_name: str
    mode: str = "ingest"
    follow_links: bool = False
    max_pages: int = 10
    metadata: Optional[dict] = None
    include_document_ids: bool = False
    dry_run: bool = False
    # Evaluation parameters
    topic: Optional[str] = None
    reviewed_by_human: bool = False
    # Audit parameters
    actor_type: str = "api"


class IngestDirectoryRequest(BaseModel):
    directory_path: str
    collection_name: str
    file_extensions: Optional[List[str]] = None
    recursive: bool = False
    metadata: Optional[dict] = None
    include_document_ids: bool = False
    mode: str = "ingest"
    # Evaluation parameters
    topic: Optional[str] = None
    reviewed_by_human: bool = False
    # Audit parameters
    actor_type: str = "api"


class AnalyzeWebsiteRequest(BaseModel):
    base_url: str
    include_url_lists: bool = False
    max_urls_per_pattern: int = 10


class UpdateCollectionMetadataRequest(BaseModel):
    new_fields: dict


class UpdateDocumentRequest(BaseModel):
    content: Optional[str] = None
    title: Optional[str] = None
    metadata: Optional[dict] = None


class ListDirectoryRequest(BaseModel):
    directory_path: str
    file_extensions: Optional[List[str]] = None
    recursive: bool = False
    include_preview: bool = False
    preview_chars: int = 500
    max_files: int = 100


# ============================================================================
# Collections
# ============================================================================

@router.get("/collections")
async def list_collections():
    """Proxy list_collections to MCP server."""
    try:
        result = await invoke_mcp_tool("list_collections", {})
        return {"collections": result}
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{name}")
async def get_collection_info(name: str):
    """Proxy get_collection_info to MCP server."""
    try:
        result = await invoke_mcp_tool("get_collection_info", {"collection_name": name})
        return result
    except Exception as e:
        logger.error(f"Error getting collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections")
async def create_collection(request: CollectionCreate):
    """Proxy create_collection to MCP server."""
    try:
        result = await invoke_mcp_tool("create_collection", {
            "name": request.name,
            "description": request.description,
            "domain": request.domain,
            "domain_scope": request.domain_scope,
        })
        return result
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{name}")
async def delete_collection(name: str):
    """Proxy delete_collection to MCP server."""
    try:
        result = await invoke_mcp_tool("delete_collection", {
            "name": name,
            "confirm": True,
        })
        return result
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Documents
# ============================================================================

@router.get("/documents")
async def list_documents(
    collection_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    include_details: bool = False,
):
    """Proxy list_documents to MCP server."""
    try:
        result = await invoke_mcp_tool("list_documents", {
            "collection_name": collection_name,
            "limit": limit,
            "offset": offset,
            "include_details": include_details,
        })
        return {"documents": result.get("documents", [])}
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}")
async def get_document(document_id: int):
    """Proxy get_document_by_id to MCP server."""
    try:
        result = await invoke_mcp_tool("get_document_by_id", {"document_id": document_id})
        return result
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """Proxy delete_document to MCP server."""
    try:
        result = await invoke_mcp_tool("delete_document", {"document_id": document_id})
        return result
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Search
# ============================================================================

@router.post("/search")
async def search_documents(request: SearchRequest):
    """Proxy search_documents to MCP server."""
    try:
        result = await invoke_mcp_tool("search_documents", {
            "query": request.query,
            "collection_name": request.collection_name,
            "limit": request.limit,
            "threshold": request.threshold,
            "include_source": request.include_source,
            "include_metadata": request.include_metadata,
            "metadata_filter": request.metadata_filter,
            # Evaluation filters
            "reviewed_by_human": request.reviewed_by_human,
            "min_quality_score": request.min_quality_score,
            "min_topic_relevance": request.min_topic_relevance,
        })
        # Results now include: reviewed_by_human, quality_score, topic_relevance_score
        return {"results": result}
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Knowledge Graph
# ============================================================================

@router.post("/graph/relationships")
async def query_relationships(request: RelationshipRequest):
    """Proxy query_relationships to MCP server."""
    try:
        params = {
            "query": request.query,
            "num_results": request.num_results,
            "threshold": request.threshold,
        }
        if request.collection_name:
            params["collection_name"] = request.collection_name
        result = await invoke_mcp_tool("query_relationships", params)
        return {"relationships": result.get("relationships", [])}
    except Exception as e:
        logger.error(f"Error querying relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graph/temporal")
async def query_temporal(request: RelationshipRequest):
    """Proxy query_temporal to MCP server."""
    try:
        params = {
            "query": request.query,
            "num_results": request.num_results,
            "threshold": request.threshold,
        }
        if request.collection_name:
            params["collection_name"] = request.collection_name
        result = await invoke_mcp_tool("query_temporal", params)
        return {"timeline": result.get("timeline", [])}
    except Exception as e:
        logger.error(f"Error querying temporal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Ingestion
# ============================================================================

@router.post("/ingest/text")
async def ingest_text(request: IngestTextRequest):
    """Proxy ingest_text to MCP server."""
    try:
        result = await invoke_mcp_tool("ingest_text", {
            "content": request.content,
            "collection_name": request.collection_name,
            "document_title": request.document_title,
            "metadata": request.metadata,
            "include_chunk_ids": request.include_chunk_ids,
            "mode": request.mode,
            # Evaluation parameters
            "topic": request.topic,
            "reviewed_by_human": request.reviewed_by_human,
            # Audit parameters
            "actor_type": request.actor_type,
        })
        return result
    except Exception as e:
        logger.error(f"Error ingesting text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/url")
async def ingest_url(request: IngestUrlRequest):
    """Proxy ingest_url to MCP server."""
    try:
        result = await invoke_mcp_tool("ingest_url", {
            "url": request.url,
            "collection_name": request.collection_name,
            "mode": request.mode,
            "follow_links": request.follow_links,
            "max_pages": request.max_pages,
            "metadata": request.metadata,
            "include_document_ids": request.include_document_ids,
            "dry_run": request.dry_run,
            # Evaluation parameters
            "topic": request.topic,
            "reviewed_by_human": request.reviewed_by_human,
            # Audit parameters
            "actor_type": request.actor_type,
        })
        return result
    except Exception as e:
        logger.error(f"Error ingesting URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# NOTE: File upload endpoint REMOVED - now handled by MCP server directly
# See src/mcp/http_routes.py for the new implementation that:
# - Processes files in-memory (no temp files)
# - Works with browser uploads via multipart/form-data
# - Frontend calls MCP server directly at /api/ingest/file


@router.post("/ingest/directory")
async def ingest_directory(request: IngestDirectoryRequest):
    """Proxy ingest_directory to MCP server."""
    try:
        result = await invoke_mcp_tool("ingest_directory", {
            "directory_path": request.directory_path,
            "collection_name": request.collection_name,
            "file_extensions": request.file_extensions,
            "recursive": request.recursive,
            "metadata": request.metadata,
            "include_document_ids": request.include_document_ids,
            "mode": request.mode,
            # Evaluation parameters
            "topic": request.topic,
            "reviewed_by_human": request.reviewed_by_human,
            # Audit parameters
            "actor_type": request.actor_type,
        })
        return result
    except Exception as e:
        logger.error(f"Error ingesting directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-website")
async def analyze_website(request: AnalyzeWebsiteRequest):
    """Proxy analyze_website to MCP server."""
    try:
        result = await invoke_mcp_tool("analyze_website", {
            "base_url": request.base_url,
            "include_url_lists": request.include_url_lists,
            "max_urls_per_pattern": request.max_urls_per_pattern,
        })
        return result
    except Exception as e:
        logger.error(f"Error analyzing website: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Metadata & Updates
# ============================================================================

@router.patch("/collections/{name}/metadata")
async def update_collection_metadata(name: str, request: UpdateCollectionMetadataRequest):
    """Proxy update_collection_metadata to MCP server."""
    try:
        result = await invoke_mcp_tool("update_collection_metadata", {
            "collection_name": name,
            "new_fields": request.new_fields,
        })
        return result
    except Exception as e:
        logger.error(f"Error updating collection metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{name}/schema")
async def get_collection_metadata_schema(name: str):
    """Proxy get_collection_metadata_schema to MCP server."""
    try:
        result = await invoke_mcp_tool("get_collection_metadata_schema", {
            "collection_name": name,
        })
        return result
    except Exception as e:
        logger.error(f"Error getting collection schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/documents/{document_id}")
async def update_document(document_id: int, request: UpdateDocumentRequest):
    """Proxy update_document to MCP server."""
    try:
        result = await invoke_mcp_tool("update_document", {
            "document_id": document_id,
            "content": request.content,
            "title": request.title,
            "metadata": request.metadata,
        })
        return result
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Utilities
# ============================================================================

@router.post("/list-directory")
async def list_directory(request: ListDirectoryRequest):
    """Proxy list_directory to MCP server."""
    try:
        result = await invoke_mcp_tool("list_directory", {
            "directory_path": request.directory_path,
            "file_extensions": request.file_extensions,
            "recursive": request.recursive,
            "include_preview": request.include_preview,
            "preview_chars": request.preview_chars,
            "max_files": request.max_files,
        })
        return result
    except Exception as e:
        logger.error(f"Error listing directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))
