/**
 * REST API functions for RAG Memory operations
 *
 * These functions call the RAG Memory MCP server indirectly through the backend.
 * The backend's ReAct agent decides which MCP tools to use based on user requests.
 */

import axios from 'axios';
import type {
  Collection,
  CollectionInfo,
  CollectionMetadataSchema,
  DocumentListItem,
  DocumentListItemDetailed,
  Document,
  SearchResult,
  RelationshipResult,
  StarterPrompt,
} from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Collections
// ============================================================================

export async function listCollections(): Promise<Collection[]> {
  const response = await api.get('/api/rag-memory/collections');
  return response.data.collections || [];
}

export async function getCollectionInfo(name: string): Promise<CollectionInfo> {
  const response = await api.get(`/api/rag-memory/collections/${name}`);
  return response.data;
}

export async function getCollectionMetadataSchema(name: string): Promise<CollectionMetadataSchema> {
  const response = await api.get(`/api/rag-memory/collections/${name}/schema`);
  return response.data;
}

export async function createCollection(
  name: string,
  description: string,
  domain: string,
  domainScope: string
): Promise<void> {
  await api.post('/api/rag-memory/collections', {
    name,
    description,
    domain,
    domain_scope: domainScope,
  });
}

export async function deleteCollection(name: string): Promise<void> {
  await api.delete(`/api/rag-memory/collections/${name}`);
}

// ============================================================================
// Documents
// ============================================================================

// Overload signatures for listDocuments
export async function listDocuments(
  collectionName?: string,
  limit?: number,
  offset?: number,
  includeDetails?: false
): Promise<DocumentListItem[]>;
export async function listDocuments(
  collectionName: string | undefined,
  limit: number | undefined,
  offset: number | undefined,
  includeDetails: true
): Promise<DocumentListItemDetailed[]>;
export async function listDocuments(
  collectionName?: string,
  limit: number = 50,
  offset: number = 0,
  includeDetails: boolean = false
): Promise<DocumentListItem[] | DocumentListItemDetailed[]> {
  const params: any = { limit, offset };
  if (collectionName) {
    params.collection_name = collectionName;
  }
  if (includeDetails) {
    params.include_details = true;
  }

  const response = await api.get('/api/rag-memory/documents', { params });
  return response.data.documents || [];
}

export async function getDocument(documentId: number): Promise<Document> {
  const response = await api.get(`/api/rag-memory/documents/${documentId}`);
  return response.data;
}

export async function deleteDocument(documentId: number): Promise<void> {
  await api.delete(`/api/rag-memory/documents/${documentId}`);
}

/**
 * Update a document's reviewed_by_human status.
 *
 * Calls the MCP server directly (same as file uploads).
 */
export async function updateDocumentReview(
  documentId: number,
  reviewedByHuman: boolean
): Promise<{ document_id: number; updated_fields: string[]; reviewed_by_human: boolean }> {
  const mcpServerUrl = import.meta.env.VITE_MCP_SERVER_URL;
  if (!mcpServerUrl) {
    throw new Error('MCP server URL not configured. Set VITE_MCP_SERVER_URL in your environment.');
  }

  const response = await fetch(`${mcpServerUrl}/api/documents/review`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      document_id: documentId,
      reviewed_by_human: reviewedByHuman,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Failed to update review status: ${response.status}`);
  }

  return response.json();
}

/**
 * Link a document to an additional collection.
 *
 * No re-embedding or re-graphing - instant metadata operation.
 * Calls the MCP server directly (same as file uploads and review updates).
 *
 * @param documentId - The document to link/unlink
 * @param collectionName - The target collection
 * @param unlink - If true, removes the document from the collection (default: false = link)
 */
export async function manageCollectionLink(
  documentId: number,
  collectionName: string,
  unlink: boolean = false
): Promise<{
  document_id: number;
  document_title: string;
  collection_name: string;
  chunks_linked?: number;
  chunks_unlinked?: number;
  status: string;
  remaining_collections?: string[];
  message: string;
}> {
  const mcpServerUrl = import.meta.env.VITE_MCP_SERVER_URL;
  if (!mcpServerUrl) {
    throw new Error('MCP server URL not configured. Set VITE_MCP_SERVER_URL in your environment.');
  }

  const response = await fetch(`${mcpServerUrl}/api/documents/manage-collection-link`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      document_id: documentId.toString(),
      collection_name: collectionName,
      unlink: unlink.toString(),
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const action = unlink ? 'unlink' : 'link';
    throw new Error(errorData.message || errorData.detail || `Failed to ${action} document: ${response.status}`);
  }

  return response.json();
}

/**
 * @deprecated Use manageCollectionLink instead. This alias is kept for backward compatibility.
 */
export async function linkDocumentToCollection(
  documentId: number,
  collectionName: string
): Promise<{ document_id: number; collection_name: string; chunks_linked: number; status: string; message: string }> {
  return manageCollectionLink(documentId, collectionName, false) as Promise<{ document_id: number; collection_name: string; chunks_linked: number; status: string; message: string }>;
}

// ============================================================================
// Search
// ============================================================================

export interface SearchOptions {
  query: string;
  collectionName?: string;
  limit?: number;
  threshold?: number;
  includeSource?: boolean;
  includeMetadata?: boolean;
  metadataFilter?: Record<string, any>;
  // Evaluation filters (all optional, default returns all)
  reviewedByHuman?: boolean;       // true=only reviewed, false=only unreviewed, undefined=all
  minQualityScore?: number;        // >= value (0.0-1.0)
  minTopicRelevance?: number;      // >= value (0.0-1.0)
}

export async function searchDocuments(
  queryOrOptions: string | SearchOptions,
  collectionName?: string,
  limit: number = 5
): Promise<SearchResult[]> {
  // Support both old (positional) and new (options) calling patterns
  let params: any;

  if (typeof queryOrOptions === 'string') {
    // Legacy calling pattern
    params = { query: queryOrOptions, limit };
    if (collectionName) {
      params.collection_name = collectionName;
    }
  } else {
    // New options pattern
    const opts = queryOrOptions;
    params = {
      query: opts.query,
      limit: opts.limit ?? 5,
    };
    if (opts.collectionName) params.collection_name = opts.collectionName;
    if (opts.threshold !== undefined) params.threshold = opts.threshold;
    if (opts.includeSource !== undefined) params.include_source = opts.includeSource;
    if (opts.includeMetadata !== undefined) params.include_metadata = opts.includeMetadata;
    if (opts.metadataFilter) params.metadata_filter = opts.metadataFilter;
    // Evaluation filters
    if (opts.reviewedByHuman !== undefined) params.reviewed_by_human = opts.reviewedByHuman;
    if (opts.minQualityScore !== undefined) params.min_quality_score = opts.minQualityScore;
    if (opts.minTopicRelevance !== undefined) params.min_topic_relevance = opts.minTopicRelevance;
  }

  const response = await api.post('/api/rag-memory/search', params);
  return response.data.results || [];
}

// ============================================================================
// Knowledge Graph
// ============================================================================

export async function queryRelationships(
  query: string,
  collectionName?: string,
  numResults: number = 5,
  threshold: number = 0.2
): Promise<RelationshipResult[]> {
  const params: any = { query, num_results: numResults, threshold };
  if (collectionName) {
    params.collection_name = collectionName;
  }

  const response = await api.post('/api/rag-memory/graph/relationships', params);
  return response.data.relationships || [];
}

export async function queryTemporal(
  query: string,
  collectionName?: string,
  numResults: number = 10,
  threshold: number = 0.2
): Promise<any[]> {
  const params: any = { query, num_results: numResults, threshold };
  if (collectionName) {
    params.collection_name = collectionName;
  }

  const response = await api.post('/api/rag-memory/graph/temporal', params);
  return response.data.timeline || [];
}

// ============================================================================
// Starter Prompts
// ============================================================================

export async function getStarterPrompts(): Promise<StarterPrompt[]> {
  const response = await api.get('/api/starter-prompts');
  return response.data;
}

// ============================================================================
// Conversations
// ============================================================================

export async function listConversations() {
  const response = await api.get('/api/conversations');
  return response.data;
}

export async function getConversation(conversationId: number) {
  const response = await api.get(`/api/conversations/${conversationId}`);
  return response.data;
}

export async function getMessages(conversationId: number) {
  const response = await api.get(`/api/conversations/${conversationId}/messages`);
  return response.data;
}

export async function deleteConversation(conversationId: number) {
  await api.delete(`/api/conversations/${conversationId}`);
}

// ============================================================================
// Admin Dashboard
// ============================================================================

export interface AdminStats {
  collections: { total: number };
  documents: { total: number; reviewed: number; unreviewed: number };
  chunks: { total: number };
  quality: {
    avg: number | null;
    min: number | null;
    max: number | null;
    distribution: { high: number; medium: number; low: number; unscored: number };
  };
  topic_relevance: {
    with_topic: number;
    without_topic: number;
    avg_relevance: number | null;
  };
}

export interface QualityAnalytics {
  quality_histogram: Array<{ range: string; count: number }>;
  topic_histogram: Array<{ range: string; count: number }>;
  review_breakdown: { reviewed: number; unreviewed: number };
  quality_by_collection: Array<{
    collection: string;
    avg: number | null;
    min: number | null;
    max: number | null;
    doc_count: number;
  }>;
  filtered_by?: string;
}

/**
 * Get aggregate system statistics for the admin dashboard.
 * Calls the MCP server's admin stats endpoint directly.
 */
export async function getAdminStats(collection?: string): Promise<AdminStats> {
  const mcpServerUrl = import.meta.env.VITE_MCP_SERVER_URL;
  if (!mcpServerUrl) {
    throw new Error('MCP server URL not configured. Set VITE_MCP_SERVER_URL in your environment.');
  }

  const url = new URL(`${mcpServerUrl}/api/admin/stats`);
  if (collection) {
    url.searchParams.set('collection', collection);
  }

  const response = await fetch(url.toString());

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Failed to get admin stats: ${response.status}`);
  }

  return response.json();
}

/**
 * Get detailed quality analytics for charts.
 * Optionally filtered by collection name.
 * Calls the MCP server's quality analytics endpoint directly.
 */
export async function getQualityAnalytics(collectionName?: string): Promise<QualityAnalytics> {
  const mcpServerUrl = import.meta.env.VITE_MCP_SERVER_URL;
  if (!mcpServerUrl) {
    throw new Error('MCP server URL not configured. Set VITE_MCP_SERVER_URL in your environment.');
  }

  const url = new URL(`${mcpServerUrl}/api/admin/analytics/quality`);
  if (collectionName) {
    url.searchParams.set('collection_name', collectionName);
  }

  const response = await fetch(url.toString());

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Failed to get quality analytics: ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// Content Analytics (Phase 2)
// ============================================================================

export interface ContentAnalytics {
  file_type_distribution: Array<{
    type: string;
    count: number;
    size_bytes: number;
    pct: number;
  }>;
  ingest_method_breakdown: Array<{
    method: string;
    count: number;
    pct: number;
  }>;
  actor_type_breakdown: Array<{
    actor: string;
    count: number;
    pct: number;
  }>;
  ingestion_timeline: Array<{
    date: string;
    total: number;
    url: number;
    file: number;
    text: number;
    directory: number;
  }>;
  crawl_stats: {
    domains: Array<{
      domain: string;
      page_count: number;
      avg_quality: number | null;
    }>;
    depth_distribution: Array<{
      depth: number;
      count: number;
      label: string;
    }>;
    total_crawl_sessions: number;
  };
  storage: {
    total_bytes: number;
    total_human: string;
    avg_per_doc: number;
    avg_human: string;
  };
  chunks: {
    total: number;
    avg_per_doc: number;
    min_per_doc: number;
    max_per_doc: number;
  };
}

/**
 * Get content composition and ingestion pattern metrics.
 * Calls the MCP server's content analytics endpoint directly.
 * @param collectionName - Optional collection to filter by
 */
export async function getContentAnalytics(collectionName?: string): Promise<ContentAnalytics> {
  const mcpServerUrl = import.meta.env.VITE_MCP_SERVER_URL;
  if (!mcpServerUrl) {
    throw new Error('MCP server URL not configured. Set VITE_MCP_SERVER_URL in your environment.');
  }

  const params = new URLSearchParams();
  if (collectionName) {
    params.set('collection', collectionName);
  }
  const queryString = params.toString();
  const url = queryString
    ? `${mcpServerUrl}/api/admin/analytics/content?${queryString}`
    : `${mcpServerUrl}/api/admin/analytics/content`;

  const response = await fetch(url);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Failed to get content analytics: ${response.status}`);
  }

  return response.json();
}
