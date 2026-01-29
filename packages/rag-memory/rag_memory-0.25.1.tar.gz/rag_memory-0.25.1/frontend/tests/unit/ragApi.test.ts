/**
 * RAG API Unit Tests
 *
 * Tests all API functions in ragApi.ts using MSW to mock backend responses.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  listCollections,
  getCollectionInfo,
  createCollection,
  deleteCollection,
  listDocuments,
  getDocument,
  deleteDocument,
  updateDocumentReview,
  manageCollectionLink,
  searchDocuments,
  queryRelationships,
  queryTemporal,
  getStarterPrompts,
  listConversations,
  getConversation,
  getMessages,
  deleteConversation as deleteConversationApi,
  getAdminStats,
  getQualityAnalytics,
  getContentAnalytics,
} from '../../src/rag/ragApi';
import { mockCollections, mockDocuments, mockSearchResults, mockConversations } from '../mocks/handlers';

// Store original fetch for MCP server calls
const originalFetch = global.fetch;

describe('ragApi', () => {
  // ============================================================================
  // Collections
  // ============================================================================

  describe('listCollections', () => {
    it('should fetch and return collections', async () => {
      const collections = await listCollections();

      expect(collections).toBeDefined();
      expect(Array.isArray(collections)).toBe(true);
      expect(collections.length).toBe(mockCollections.length);
      expect(collections[0].name).toBe('test-collection');
    });
  });

  describe('getCollectionInfo', () => {
    it('should fetch collection details', async () => {
      const info = await getCollectionInfo('test-collection');

      expect(info).toBeDefined();
      expect(info.name).toBe('test-collection');
      expect(info.chunk_count).toBeDefined();
      expect(info.sample_documents).toBeDefined();
    });

    it('should throw error for non-existent collection', async () => {
      await expect(getCollectionInfo('non-existent')).rejects.toThrow();
    });
  });

  describe('createCollection', () => {
    it('should create a new collection', async () => {
      // Should not throw
      await createCollection('new-collection', 'Description', 'engineering', 'Test scope');
    });
  });

  describe('deleteCollection', () => {
    it('should delete a collection', async () => {
      // Should not throw
      await deleteCollection('test-collection');
    });
  });

  // ============================================================================
  // Documents
  // ============================================================================

  describe('listDocuments', () => {
    it('should fetch documents without filters', async () => {
      const documents = await listDocuments();

      expect(documents).toBeDefined();
      expect(Array.isArray(documents)).toBe(true);
      expect(documents.length).toBe(mockDocuments.length);
    });

    it('should fetch documents with collection filter', async () => {
      const documents = await listDocuments('test-collection');

      expect(documents).toBeDefined();
      expect(Array.isArray(documents)).toBe(true);
    });

    it('should support pagination params', async () => {
      const documents = await listDocuments(undefined, 10, 5);

      expect(documents).toBeDefined();
      expect(Array.isArray(documents)).toBe(true);
    });
  });

  describe('getDocument', () => {
    it('should fetch a single document by ID', async () => {
      const document = await getDocument(1);

      expect(document).toBeDefined();
      expect(document.id).toBe(1);
      expect(document.content).toBeDefined();
      expect(document.file_type).toBeDefined();
    });

    it('should throw error for non-existent document', async () => {
      await expect(getDocument(9999)).rejects.toThrow();
    });
  });

  describe('deleteDocument', () => {
    it('should delete a document', async () => {
      // Should not throw
      await deleteDocument(1);
    });
  });

  describe('updateDocumentReview', () => {
    // These tests mock fetch directly since updateDocumentReview uses fetch, not axios
    let mockFetch: ReturnType<typeof vi.fn>;

    beforeEach(() => {
      mockFetch = vi.fn();
      global.fetch = mockFetch as unknown as typeof fetch;
      // Set env var for MCP server URL
      vi.stubEnv('VITE_MCP_SERVER_URL', 'http://localhost:3001');
    });

    afterEach(() => {
      global.fetch = originalFetch;
      vi.unstubAllEnvs();
    });

    it('should update review status to true', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          document_id: 1,
          updated_fields: ['reviewed_by_human'],
          reviewed_by_human: true,
        }),
      });

      const result = await updateDocumentReview(1, true);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:3001/api/documents/review',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ document_id: 1, reviewed_by_human: true }),
        })
      );
      expect(result.reviewed_by_human).toBe(true);
    });

    it('should throw error on non-ok response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ message: 'Server error' }),
      });

      await expect(updateDocumentReview(1, true)).rejects.toThrow('Server error');
    });
  });

  describe('manageCollectionLink', () => {
    let mockFetch: ReturnType<typeof vi.fn>;

    beforeEach(() => {
      mockFetch = vi.fn();
      global.fetch = mockFetch as unknown as typeof fetch;
      vi.stubEnv('VITE_MCP_SERVER_URL', 'http://localhost:3001');
    });

    afterEach(() => {
      global.fetch = originalFetch;
      vi.unstubAllEnvs();
    });

    it('should link document to collection', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          document_id: 1,
          document_title: 'test.md',
          collection_name: 'new-collection',
          chunks_linked: 5,
          status: 'linked',
          message: 'Document linked successfully',
        }),
      });

      const result = await manageCollectionLink(1, 'new-collection', false);

      expect(result.status).toBe('linked');
      expect(result.chunks_linked).toBe(5);
    });

    it('should unlink document from collection', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          document_id: 1,
          document_title: 'test.md',
          collection_name: 'old-collection',
          chunks_unlinked: 5,
          status: 'unlinked',
          remaining_collections: ['other-collection'],
          message: 'Document unlinked successfully',
        }),
      });

      const result = await manageCollectionLink(1, 'old-collection', true);

      expect(result.status).toBe('unlinked');
      expect(result.chunks_unlinked).toBe(5);
    });
  });

  // ============================================================================
  // Search
  // ============================================================================

  describe('searchDocuments', () => {
    it('should search with string query', async () => {
      const results = await searchDocuments('test query');

      expect(results).toBeDefined();
      expect(Array.isArray(results)).toBe(true);
      expect(results.length).toBe(mockSearchResults.length);
      expect(results[0].similarity).toBeGreaterThan(0);
    });

    it('should search with collection filter', async () => {
      const results = await searchDocuments('test query', 'test-collection');

      expect(results).toBeDefined();
      expect(Array.isArray(results)).toBe(true);
    });

    it('should accept options object', async () => {
      const results = await searchDocuments({
        query: 'test query',
        collectionName: 'test-collection',
        limit: 10,
        threshold: 0.5,
        reviewedByHuman: true,
        minQualityScore: 0.7,
      });

      expect(results).toBeDefined();
      expect(Array.isArray(results)).toBe(true);
    });
  });

  // ============================================================================
  // Knowledge Graph
  // ============================================================================

  describe('queryRelationships', () => {
    it('should query relationships', async () => {
      const results = await queryRelationships('How are concepts related?');

      expect(results).toBeDefined();
      expect(Array.isArray(results)).toBe(true);
      expect(results[0]).toHaveProperty('relationship_type');
      expect(results[0]).toHaveProperty('fact');
    });

    it('should query with collection filter', async () => {
      const results = await queryRelationships('How are concepts related?', 'test-collection');

      expect(results).toBeDefined();
      expect(Array.isArray(results)).toBe(true);
    });
  });

  describe('queryTemporal', () => {
    it('should query temporal data', async () => {
      const results = await queryTemporal('How has this evolved?');

      expect(results).toBeDefined();
      expect(Array.isArray(results)).toBe(true);
      expect(results[0]).toHaveProperty('fact');
      expect(results[0]).toHaveProperty('valid_from');
      expect(results[0]).toHaveProperty('status');
    });

    it('should query with collection filter', async () => {
      const results = await queryTemporal('How has this evolved?', 'test-collection', 5, 0.3);

      expect(results).toBeDefined();
      expect(Array.isArray(results)).toBe(true);
    });
  });

  // ============================================================================
  // Starter Prompts
  // ============================================================================

  describe('getStarterPrompts', () => {
    it('should fetch starter prompts', async () => {
      const prompts = await getStarterPrompts();

      expect(prompts).toBeDefined();
      expect(Array.isArray(prompts)).toBe(true);
      expect(prompts[0]).toHaveProperty('title');
      expect(prompts[0]).toHaveProperty('prompt');
    });
  });

  // ============================================================================
  // Conversations
  // ============================================================================

  describe('listConversations', () => {
    it('should fetch conversations', async () => {
      const conversations = await listConversations();

      expect(conversations).toBeDefined();
      expect(Array.isArray(conversations)).toBe(true);
      expect(conversations.length).toBe(mockConversations.length);
    });
  });

  describe('getConversation', () => {
    it('should fetch a single conversation', async () => {
      const conversation = await getConversation(1);

      expect(conversation).toBeDefined();
      expect(conversation.id).toBe(1);
      expect(conversation.title).toBeDefined();
    });

    it('should throw error for non-existent conversation', async () => {
      await expect(getConversation(9999)).rejects.toThrow();
    });
  });

  describe('getMessages', () => {
    it('should fetch messages for a conversation', async () => {
      const messages = await getMessages(1);

      expect(messages).toBeDefined();
      expect(Array.isArray(messages)).toBe(true);
      expect(messages.length).toBeGreaterThan(0);
      expect(messages[0]).toHaveProperty('role');
      expect(messages[0]).toHaveProperty('content');
    });
  });

  describe('deleteConversation (API)', () => {
    it('should delete a conversation', async () => {
      // Should not throw
      await deleteConversationApi(1);
    });
  });

  // ============================================================================
  // Admin Dashboard
  // ============================================================================

  describe('getAdminStats', () => {
    let mockFetch: ReturnType<typeof vi.fn>;

    beforeEach(() => {
      mockFetch = vi.fn();
      global.fetch = mockFetch as unknown as typeof fetch;
      vi.stubEnv('VITE_MCP_SERVER_URL', 'http://localhost:3001');
    });

    afterEach(() => {
      global.fetch = originalFetch;
      vi.unstubAllEnvs();
    });

    it('should fetch admin stats', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          collections: { total: 5 },
          documents: { total: 100, reviewed: 30, unreviewed: 70 },
          chunks: { total: 500 },
          quality: { avg: 0.75, min: 0.4, max: 0.95, distribution: { high: 20, medium: 50, low: 30, unscored: 0 } },
          topic_relevance: { with_topic: 60, without_topic: 40, avg_relevance: 0.68 },
        }),
      });

      const stats = await getAdminStats();

      expect(stats).toBeDefined();
      expect(stats.collections.total).toBe(5);
      expect(stats.documents.total).toBe(100);
      expect(stats.quality.avg).toBe(0.75);
    });

    it('should fetch admin stats filtered by collection', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          collections: { total: 1 },
          documents: { total: 20, reviewed: 10, unreviewed: 10 },
          chunks: { total: 100 },
          quality: { avg: 0.8, min: 0.6, max: 0.95, distribution: { high: 10, medium: 8, low: 2, unscored: 0 } },
          topic_relevance: { with_topic: 15, without_topic: 5, avg_relevance: 0.72 },
        }),
      });

      const stats = await getAdminStats('test-collection');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('collection=test-collection')
      );
      expect(stats.collections.total).toBe(1);
    });
  });

  describe('getQualityAnalytics', () => {
    let mockFetch: ReturnType<typeof vi.fn>;

    beforeEach(() => {
      mockFetch = vi.fn();
      global.fetch = mockFetch as unknown as typeof fetch;
      vi.stubEnv('VITE_MCP_SERVER_URL', 'http://localhost:3001');
    });

    afterEach(() => {
      global.fetch = originalFetch;
      vi.unstubAllEnvs();
    });

    it('should fetch quality analytics', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          quality_histogram: [
            { range: '0.0-0.2', count: 5 },
            { range: '0.2-0.4', count: 10 },
          ],
          topic_histogram: [
            { range: '0.0-0.2', count: 3 },
          ],
          review_breakdown: { reviewed: 30, unreviewed: 70 },
          quality_by_collection: [
            { collection: 'test', avg: 0.75, min: 0.4, max: 0.95, doc_count: 50 },
          ],
        }),
      });

      const analytics = await getQualityAnalytics();

      expect(analytics).toBeDefined();
      expect(analytics.quality_histogram).toBeDefined();
      expect(analytics.review_breakdown.reviewed).toBe(30);
    });

    it('should filter by collection', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          quality_histogram: [],
          topic_histogram: [],
          review_breakdown: { reviewed: 10, unreviewed: 10 },
          quality_by_collection: [],
          filtered_by: 'test-collection',
        }),
      });

      await getQualityAnalytics('test-collection');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('collection_name=test-collection')
      );
    });
  });

  describe('getContentAnalytics', () => {
    let mockFetch: ReturnType<typeof vi.fn>;

    beforeEach(() => {
      mockFetch = vi.fn();
      global.fetch = mockFetch as unknown as typeof fetch;
      vi.stubEnv('VITE_MCP_SERVER_URL', 'http://localhost:3001');
    });

    afterEach(() => {
      global.fetch = originalFetch;
      vi.unstubAllEnvs();
    });

    it('should fetch content analytics', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          file_type_distribution: [
            { type: 'text/markdown', count: 50, size_bytes: 100000, pct: 50 },
          ],
          ingest_method_breakdown: [
            { method: 'url', count: 60, pct: 60 },
          ],
          actor_type_breakdown: [
            { actor: 'agent', count: 80, pct: 80 },
          ],
          ingestion_timeline: [
            { date: '2024-01-01', total: 10, url: 5, file: 3, text: 2, directory: 0 },
          ],
          crawl_stats: {
            domains: [{ domain: 'example.com', page_count: 20, avg_quality: 0.75 }],
            depth_distribution: [{ depth: 1, count: 10, label: 'Level 1' }],
            total_crawl_sessions: 5,
          },
          storage: {
            total_bytes: 1000000,
            total_human: '977 KB',
            avg_per_doc: 10000,
            avg_human: '9.77 KB',
          },
          chunks: { total: 500, avg_per_doc: 5, min_per_doc: 1, max_per_doc: 20 },
        }),
      });

      const analytics = await getContentAnalytics();

      expect(analytics).toBeDefined();
      expect(analytics.file_type_distribution).toBeDefined();
      expect(analytics.storage.total_bytes).toBe(1000000);
      expect(analytics.chunks.total).toBe(500);
    });

    it('should filter by collection', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          file_type_distribution: [],
          ingest_method_breakdown: [],
          actor_type_breakdown: [],
          ingestion_timeline: [],
          crawl_stats: { domains: [], depth_distribution: [], total_crawl_sessions: 0 },
          storage: { total_bytes: 0, total_human: '0 B', avg_per_doc: 0, avg_human: '0 B' },
          chunks: { total: 0, avg_per_doc: 0, min_per_doc: 0, max_per_doc: 0 },
        }),
      });

      await getContentAnalytics('test-collection');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('collection=test-collection')
      );
    });

    it('should throw error on non-ok response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ message: 'Failed to get analytics' }),
      });

      await expect(getContentAnalytics()).rejects.toThrow('Failed to get analytics');
    });
  });
});
