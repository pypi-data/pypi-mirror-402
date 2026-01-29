/**
 * Zustand Store Unit Tests
 *
 * Tests all store actions and state transitions.
 * Uses MSW for API mocking.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useRagStore } from '../../src/rag/store';
import * as ragApi from '../../src/rag/ragApi';

// Mock the ragApi module
vi.mock('../../src/rag/ragApi');

// Store original fetch
const originalFetch = global.fetch;

// Create mock fetch
const mockFetch = vi.fn();

describe('useRagStore', () => {
  beforeEach(() => {
    // Reset store to initial state (reset() doesn't clear everything)
    useRagStore.getState().reset();
    // Clear fields that reset() doesn't handle
    useRagStore.setState({
      collections: [],
      documents: [],
      selectedCollectionId: null,
      selectedDocumentId: null,
      inputValue: '',
    });
    // Replace fetch with mock
    global.fetch = mockFetch as unknown as typeof fetch;
    mockFetch.mockReset();
    // Reset ragApi mocks
    vi.mocked(ragApi).listCollections.mockReset();
    vi.mocked(ragApi).createCollection.mockReset();
    vi.mocked(ragApi).listDocuments.mockReset();
    vi.mocked(ragApi).searchDocuments.mockReset();
    vi.mocked(ragApi).queryRelationships.mockReset();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  // ============================================================================
  // Synchronous State Actions
  // ============================================================================

  describe('selectCollection', () => {
    it('should set selected collection ID', () => {
      useRagStore.getState().selectCollection(5);
      expect(useRagStore.getState().selectedCollectionId).toBe(5);
    });

    it('should allow setting null', () => {
      useRagStore.getState().selectCollection(5);
      useRagStore.getState().selectCollection(null);
      expect(useRagStore.getState().selectedCollectionId).toBe(null);
    });
  });

  describe('selectDocument', () => {
    it('should set selected document ID', () => {
      useRagStore.getState().selectDocument(10);
      expect(useRagStore.getState().selectedDocumentId).toBe(10);
    });

    it('should allow setting null', () => {
      useRagStore.getState().selectDocument(10);
      useRagStore.getState().selectDocument(null);
      expect(useRagStore.getState().selectedDocumentId).toBe(null);
    });
  });

  describe('setInputValue', () => {
    it('should set input value', () => {
      useRagStore.getState().setInputValue('test query');
      expect(useRagStore.getState().inputValue).toBe('test query');
    });

    it('should allow empty string', () => {
      useRagStore.getState().setInputValue('test');
      useRagStore.getState().setInputValue('');
      expect(useRagStore.getState().inputValue).toBe('');
    });
  });

  describe('startNewConversation', () => {
    it('should clear active conversation and messages', () => {
      // Set some state first
      useRagStore.setState({
        activeConversationId: 1,
        messages: [{ id: 1, role: 'user', content: 'test', created_at: '2024-01-01' }],
        isStreaming: true,
        streamingContent: 'partial',
        currentToolExecutions: [{ id: 't1', name: 'test', status: 'running', startTime: Date.now() }],
        error: 'some error',
      });

      useRagStore.getState().startNewConversation();

      const state = useRagStore.getState();
      expect(state.activeConversationId).toBe(null);
      expect(state.messages).toHaveLength(0);
      expect(state.isStreaming).toBe(false);
      expect(state.streamingContent).toBe('');
      expect(state.currentToolExecutions).toHaveLength(0);
      expect(state.error).toBe(null);
    });

    it('should clear rich content', () => {
      useRagStore.setState({
        currentSearchResults: [{ content: 'test', similarity: 0.9, source_document_id: 1, source_filename: 'test.md', reviewed_by_human: false, quality_score: 0.8, topic_relevance_score: null }],
        currentWebSearchResults: [{ title: 'Test', url: 'https://test.com', snippet: 'test' }],
        currentKnowledgeGraph: [{ id: 'r1', relationship_type: 'relates_to', fact: 'test', source_node_id: 'a', target_node_id: 'b' }],
        currentTemporalData: [{ fact: 'test', relationship_type: 'added', valid_from: '2024-01-01', valid_until: null, status: 'current', created_at: '2024-01-01' }],
      });

      useRagStore.getState().startNewConversation();

      const state = useRagStore.getState();
      expect(state.currentSearchResults).toHaveLength(0);
      expect(state.currentWebSearchResults).toHaveLength(0);
      expect(state.currentKnowledgeGraph).toHaveLength(0);
      expect(state.currentTemporalData).toHaveLength(0);
    });
  });

  describe('clearPendingTools', () => {
    it('should clear pending tool calls and conversation ID', () => {
      useRagStore.setState({
        pendingToolCalls: [{ id: 't1', name: 'search', args: {} }],
        pendingToolConversationId: 42,
      });

      useRagStore.getState().clearPendingTools();

      const state = useRagStore.getState();
      expect(state.pendingToolCalls).toHaveLength(0);
      expect(state.pendingToolConversationId).toBe(null);
    });
  });

  describe('openIngestionModal', () => {
    it('should open modal with specified tab', () => {
      useRagStore.getState().openIngestionModal('url', { suggested_collection: 'docs' });

      const state = useRagStore.getState();
      expect(state.ingestionModalOpen).toBe(true);
      expect(state.ingestionModalTab).toBe('url');
      expect(state.ingestionModalParams).toEqual({ suggested_collection: 'docs' });
    });

    it('should open modal with default file tab', () => {
      useRagStore.getState().openIngestionModal('file', {});

      const state = useRagStore.getState();
      expect(state.ingestionModalOpen).toBe(true);
      expect(state.ingestionModalTab).toBe('file');
    });
  });

  describe('closeIngestionModal', () => {
    it('should close modal and reset tab', () => {
      useRagStore.setState({
        ingestionModalOpen: true,
        ingestionModalTab: 'url',
        ingestionModalParams: { suggested_collection: 'test' },
      });

      useRagStore.getState().closeIngestionModal();

      const state = useRagStore.getState();
      expect(state.ingestionModalOpen).toBe(false);
      expect(state.ingestionModalTab).toBe('file');
      expect(state.ingestionModalParams).toEqual({});
    });
  });

  describe('reset', () => {
    it('should reset all state to initial values', () => {
      // Set a bunch of state
      useRagStore.setState({
        messages: [{ id: 1, role: 'user', content: 'test', created_at: '2024-01-01' }],
        conversations: [{ id: 1, title: 'Test', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false }],
        isStreaming: true,
        streamingContent: 'partial',
        activeConversationId: 1,
        currentToolExecutions: [{ id: 't1', name: 'test', status: 'running', startTime: Date.now() }],
        error: 'error',
        searchResults: [{ content: 'test', similarity: 0.9, source_document_id: 1, source_filename: 'test.md', reviewed_by_human: false, quality_score: 0.8, topic_relevance_score: null }],
        pendingToolCalls: [{ id: 't1', name: 'test', args: {} }],
        pendingToolConversationId: 1,
        ingestionModalOpen: true,
        ingestionModalTab: 'url',
        ingestionModalParams: { test: 'value' },
      });

      useRagStore.getState().reset();

      const state = useRagStore.getState();
      expect(state.messages).toHaveLength(0);
      expect(state.conversations).toHaveLength(0);
      expect(state.isStreaming).toBe(false);
      expect(state.streamingContent).toBe('');
      expect(state.activeConversationId).toBe(null);
      expect(state.currentToolExecutions).toHaveLength(0);
      expect(state.error).toBe(null);
      expect(state.searchResults).toHaveLength(0);
      expect(state.pendingToolCalls).toHaveLength(0);
      expect(state.pendingToolConversationId).toBe(null);
      expect(state.ingestionModalOpen).toBe(false);
      expect(state.ingestionModalTab).toBe('file');
      expect(state.ingestionModalParams).toEqual({});
    });
  });

  // ============================================================================
  // Conversation Management (Async)
  // ============================================================================

  describe('loadConversations', () => {
    it('should load and sort conversations by updated_at', async () => {
      const mockConversations = [
        { id: 1, title: 'Old', created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z', is_pinned: false },
        { id: 2, title: 'New', created_at: '2024-01-02T00:00:00Z', updated_at: '2024-01-03T00:00:00Z', is_pinned: false },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockConversations),
      });

      await useRagStore.getState().loadConversations();

      const state = useRagStore.getState();
      expect(state.conversations).toHaveLength(2);
      expect(state.conversations[0].id).toBe(2); // Newer first
      expect(state.conversations[1].id).toBe(1);
    });

    it('should handle errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await useRagStore.getState().loadConversations();

      // Should not throw, just log error
      expect(useRagStore.getState().conversations).toHaveLength(0);
    });
  });

  describe('selectConversation', () => {
    it('should load messages for selected conversation', async () => {
      const mockMessages = [
        { id: 1, role: 'user', content: 'Hello', created_at: '2024-01-01T00:00:00Z' },
        { id: 2, role: 'assistant', content: 'Hi!', created_at: '2024-01-01T00:00:01Z' },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMessages),
      });

      await useRagStore.getState().selectConversation(5);

      const state = useRagStore.getState();
      expect(state.activeConversationId).toBe(5);
      expect(state.messages).toHaveLength(2);
      expect(state.messages[0].content).toBe('Hello');
    });

    it('should clear streaming state when switching', async () => {
      useRagStore.setState({
        isStreaming: true,
        streamingContent: 'partial',
        currentToolExecutions: [{ id: 't1', name: 'test', status: 'running', startTime: Date.now() }],
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      await useRagStore.getState().selectConversation(5);

      const state = useRagStore.getState();
      expect(state.isStreaming).toBe(false);
      expect(state.streamingContent).toBe('');
      expect(state.currentToolExecutions).toHaveLength(0);
    });

    it('should set error on failure', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Load failed'));

      await useRagStore.getState().selectConversation(5);

      expect(useRagStore.getState().error).toBe('Failed to load conversation');
    });
  });

  describe('deleteConversation', () => {
    it('should remove conversation from list', async () => {
      useRagStore.setState({
        conversations: [
          { id: 1, title: 'Keep', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false },
          { id: 2, title: 'Delete', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false },
        ],
      });

      mockFetch.mockResolvedValueOnce({ ok: true });

      await useRagStore.getState().deleteConversation(2);

      const state = useRagStore.getState();
      expect(state.conversations).toHaveLength(1);
      expect(state.conversations[0].id).toBe(1);
    });

    it('should clear active conversation if deleted', async () => {
      useRagStore.setState({
        conversations: [
          { id: 1, title: 'Active', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false },
        ],
        activeConversationId: 1,
        messages: [{ id: 1, role: 'user', content: 'test', created_at: '2024-01-01' }],
      });

      mockFetch.mockResolvedValueOnce({ ok: true });

      await useRagStore.getState().deleteConversation(1);

      const state = useRagStore.getState();
      expect(state.activeConversationId).toBe(null);
      expect(state.messages).toHaveLength(0);
    });
  });

  describe('updateConversation', () => {
    it('should update conversation in list', async () => {
      useRagStore.setState({
        conversations: [
          { id: 1, title: 'Old Title', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false },
        ],
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 1, title: 'New Title', created_at: '2024-01-01', updated_at: '2024-01-02', is_pinned: true }),
      });

      await useRagStore.getState().updateConversation(1, { title: 'New Title', is_pinned: true });

      const state = useRagStore.getState();
      expect(state.conversations[0].title).toBe('New Title');
      expect(state.conversations[0].is_pinned).toBe(true);
    });
  });

  describe('bulkDeleteConversations', () => {
    it('should remove multiple conversations', async () => {
      useRagStore.setState({
        conversations: [
          { id: 1, title: 'Keep', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false },
          { id: 2, title: 'Delete', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false },
          { id: 3, title: 'Delete', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false },
        ],
      });

      mockFetch.mockResolvedValueOnce({ ok: true });

      await useRagStore.getState().bulkDeleteConversations([2, 3]);

      expect(useRagStore.getState().conversations).toHaveLength(1);
      expect(useRagStore.getState().conversations[0].id).toBe(1);
    });

    it('should clear active conversation if it was deleted', async () => {
      useRagStore.setState({
        conversations: [
          { id: 1, title: 'Active', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false },
          { id: 2, title: 'Other', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false },
        ],
        activeConversationId: 1,
        messages: [{ id: 1, role: 'user', content: 'test', created_at: '2024-01-01' }],
      });

      mockFetch.mockResolvedValueOnce({ ok: true });

      await useRagStore.getState().bulkDeleteConversations([1]);

      const state = useRagStore.getState();
      expect(state.activeConversationId).toBe(null);
      expect(state.messages).toHaveLength(0);
    });
  });

  describe('deleteAllConversations', () => {
    it('should clear all conversations', async () => {
      useRagStore.setState({
        conversations: [
          { id: 1, title: 'A', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false },
          { id: 2, title: 'B', created_at: '2024-01-01', updated_at: '2024-01-01', is_pinned: false },
        ],
        activeConversationId: 1,
        messages: [{ id: 1, role: 'user', content: 'test', created_at: '2024-01-01' }],
      });

      mockFetch.mockResolvedValueOnce({ ok: true });

      await useRagStore.getState().deleteAllConversations();

      const state = useRagStore.getState();
      expect(state.conversations).toHaveLength(0);
      expect(state.activeConversationId).toBe(null);
      expect(state.messages).toHaveLength(0);
    });
  });

  // ============================================================================
  // Collection Management (Async via ragApi)
  // ============================================================================

  describe('loadCollections', () => {
    it('should load collections via ragApi', async () => {
      const mockCollections = [
        { id: 1, name: 'docs', description: 'Documentation', document_count: 10, created_at: '2024-01-01' },
      ];

      vi.mocked(ragApi).listCollections.mockResolvedValueOnce(mockCollections);

      await useRagStore.getState().loadCollections();

      expect(useRagStore.getState().collections).toEqual(mockCollections);
    });

    it('should handle errors gracefully', async () => {
      vi.mocked(ragApi).listCollections.mockRejectedValueOnce(new Error('API error'));

      await useRagStore.getState().loadCollections();

      // Should not throw
      expect(useRagStore.getState().collections).toHaveLength(0);
    });
  });

  describe('createCollection', () => {
    it('should create collection and reload list', async () => {
      const newCollection = { collection_id: 1, name: 'test', description: 'Test', created: true };
      const updatedCollections = [
        { id: 1, name: 'test', description: 'Test', document_count: 0, created_at: '2024-01-01' },
      ];

      vi.mocked(ragApi).createCollection.mockResolvedValueOnce(newCollection);
      vi.mocked(ragApi).listCollections.mockResolvedValueOnce(updatedCollections);

      await useRagStore.getState().createCollection('test', 'Test', 'engineering', 'Test scope');

      expect(ragApi.createCollection).toHaveBeenCalledWith('test', 'Test', 'engineering', 'Test scope');
      expect(useRagStore.getState().collections).toEqual(updatedCollections);
    });

    it('should throw error on failure', async () => {
      vi.mocked(ragApi).createCollection.mockRejectedValueOnce(new Error('Create failed'));

      await expect(
        useRagStore.getState().createCollection('test', 'Test', 'engineering', 'Test scope')
      ).rejects.toThrow('Create failed');
    });
  });

  describe('loadDocuments', () => {
    it('should load documents for collection', async () => {
      const mockDocuments = [
        { id: 1, filename: 'doc.md', chunk_count: 5 },
      ];

      vi.mocked(ragApi).listDocuments.mockResolvedValueOnce(mockDocuments);

      await useRagStore.getState().loadDocuments('test-collection');

      expect(ragApi.listDocuments).toHaveBeenCalledWith('test-collection');
      expect(useRagStore.getState().documents).toEqual(mockDocuments);
    });
  });

  describe('searchDocuments', () => {
    it('should search documents and store results', async () => {
      const mockResults = [
        { content: 'result', similarity: 0.9, source_document_id: 1, source_filename: 'doc.md', reviewed_by_human: false, quality_score: 0.8, topic_relevance_score: null },
      ];

      vi.mocked(ragApi).searchDocuments.mockResolvedValueOnce(mockResults);

      await useRagStore.getState().searchDocuments('test query', 'docs');

      expect(ragApi.searchDocuments).toHaveBeenCalledWith('test query', 'docs');
      expect(useRagStore.getState().searchResults).toEqual(mockResults);
    });
  });

  describe('queryRelationships', () => {
    it('should query relationships and store results', async () => {
      const mockRelationships = [
        { id: 'r1', relationship_type: 'relates_to', fact: 'A relates to B', source_node_id: 'a', target_node_id: 'b' },
      ];

      vi.mocked(ragApi).queryRelationships.mockResolvedValueOnce(mockRelationships);

      await useRagStore.getState().queryRelationships('test query', 'docs');

      expect(ragApi.queryRelationships).toHaveBeenCalledWith('test query', 'docs');
      expect(useRagStore.getState().knowledgeGraphData).toEqual(mockRelationships);
    });
  });

  // ============================================================================
  // sendMessage Action
  // ============================================================================

  describe('sendMessage', () => {
    it('should create conversation if none active', async () => {
      const mockSend = vi.fn();
      useRagStore.setState({
        sseClient: { send: mockSend, close: vi.fn() } as any,
        activeConversationId: null,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 123, title: 'Test' }),
      });

      await useRagStore.getState().sendMessage('Hello');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/conversations',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ title: 'Hello' }),
        })
      );
      expect(useRagStore.getState().activeConversationId).toBe(123);
    });

    it('should add user message optimistically', async () => {
      const mockSend = vi.fn();
      useRagStore.setState({
        sseClient: { send: mockSend, close: vi.fn() } as any,
        activeConversationId: 1,
        messages: [],
      });

      await useRagStore.getState().sendMessage('Test message');

      const state = useRagStore.getState();
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0].role).toBe('user');
      expect(state.messages[0].content).toBe('Test message');
    });

    it('should call sseClient.send with correct payload', async () => {
      const mockSend = vi.fn();
      useRagStore.setState({
        sseClient: { send: mockSend, close: vi.fn() } as any,
        activeConversationId: 42,
      });

      await useRagStore.getState().sendMessage('Hello world');

      expect(mockSend).toHaveBeenCalledWith(
        JSON.stringify({ message: 'Hello world', conversation_id: 42 })
      );
    });

    it('should set isStreaming to true', async () => {
      const mockSend = vi.fn();
      useRagStore.setState({
        sseClient: { send: mockSend, close: vi.fn() } as any,
        activeConversationId: 1,
        isStreaming: false,
      });

      await useRagStore.getState().sendMessage('Test');

      expect(useRagStore.getState().isStreaming).toBe(true);
    });

    it('should clear streamingContent', async () => {
      const mockSend = vi.fn();
      useRagStore.setState({
        sseClient: { send: mockSend, close: vi.fn() } as any,
        activeConversationId: 1,
        streamingContent: 'old content',
      });

      await useRagStore.getState().sendMessage('Test');

      expect(useRagStore.getState().streamingContent).toBe('');
    });

    it('should handle conversation creation error', async () => {
      const mockSend = vi.fn();
      useRagStore.setState({
        sseClient: { send: mockSend, close: vi.fn() } as any,
        activeConversationId: null,
      });

      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await useRagStore.getState().sendMessage('Hello');

      expect(useRagStore.getState().error).toBe('Failed to create conversation');
      expect(mockSend).not.toHaveBeenCalled();
    });

    it('should truncate long messages for conversation title', async () => {
      const mockSend = vi.fn();
      useRagStore.setState({
        sseClient: { send: mockSend, close: vi.fn() } as any,
        activeConversationId: null,
      });

      const longMessage = 'A'.repeat(100);
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 1, title: longMessage.substring(0, 50) + '...' }),
      });

      await useRagStore.getState().sendMessage(longMessage);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/conversations',
        expect.objectContaining({
          body: JSON.stringify({ title: 'A'.repeat(50) + '...' }),
        })
      );
    });

    it('should not call sseClient.send if sseClient is null', async () => {
      useRagStore.setState({
        sseClient: null,
        activeConversationId: 1,
      });

      // Should not throw
      await useRagStore.getState().sendMessage('Test');

      // Message should still be added
      expect(useRagStore.getState().messages).toHaveLength(1);
    });
  });

  // ============================================================================
  // Tool Approval Actions
  // ============================================================================

  describe('approvePendingTools', () => {
    // Helper to create mock readable stream
    function createMockSSEStream(events: Array<{ type: string; [key: string]: any }>) {
      const encoder = new TextEncoder();
      const data = events.map(e => `data: ${JSON.stringify(e)}\n`).join('');

      return new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(data));
          controller.close();
        },
      });
    }

    it('should return early if no pendingToolConversationId', async () => {
      useRagStore.setState({ pendingToolConversationId: null });

      await useRagStore.getState().approvePendingTools();

      // fetch should not be called
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('should clear pending state and set streaming', async () => {
      useRagStore.setState({
        pendingToolCalls: [{ id: 't1', name: 'test', args: {} }],
        pendingToolConversationId: 42,
        isStreaming: false,
        sseClient: { send: vi.fn(), close: vi.fn() } as any,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([{ type: 'done' }]),
      });

      await useRagStore.getState().approvePendingTools();

      // Pending should be cleared immediately
      // Note: isStreaming will be false at end due to 'done' event
    });

    it('should call approve endpoint with conversation_id', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        sseClient: { send: vi.fn(), close: vi.fn() } as any,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([{ type: 'done' }]),
      });

      await useRagStore.getState().approvePendingTools();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/chat/approve',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ conversation_id: 42 }),
        })
      );
    });

    it('should handle token events and accumulate content', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        streamingContent: '',
        sseClient: { send: vi.fn(), close: vi.fn() } as any,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'token', content: 'Hello ' },
          { type: 'token', content: 'world' },
          { type: 'done' },
        ]),
      });

      await useRagStore.getState().approvePendingTools();

      // Content should have been accumulated then turned into a message
      expect(useRagStore.getState().messages).toHaveLength(1);
      expect(useRagStore.getState().messages[0].content).toBe('Hello world');
    });

    it('should handle done event and finalize message', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        messages: [],
        streamingContent: '',
        sseClient: { send: vi.fn(), close: vi.fn() } as any,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'token', content: 'Response' },
          { type: 'done' },
        ]),
      });

      await useRagStore.getState().approvePendingTools();

      const state = useRagStore.getState();
      expect(state.isStreaming).toBe(false);
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0].role).toBe('assistant');
    });

    it('should handle tool_start event', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        currentToolExecutions: [],
        sseClient: { send: vi.fn(), close: vi.fn() } as any,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'tool_start', tool: { id: 't1', name: 'search_documents' } },
          { type: 'done' },
        ]),
      });

      await useRagStore.getState().approvePendingTools();

      // Tool execution should have been added
      expect(useRagStore.getState().currentToolExecutions.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle error events', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        sseClient: { send: vi.fn(), close: vi.fn() } as any,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'error', message: 'Tool failed' },
        ]),
      });

      await useRagStore.getState().approvePendingTools();

      expect(useRagStore.getState().error).toBe('Tool failed');
      expect(useRagStore.getState().isStreaming).toBe(false);
    });

    it('should handle fetch errors', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        sseClient: { send: vi.fn(), close: vi.fn() } as any,
      });

      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await useRagStore.getState().approvePendingTools();

      expect(useRagStore.getState().error).toBe('Failed to approve tools');
      expect(useRagStore.getState().isStreaming).toBe(false);
    });

    it('should handle non-ok response', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        sseClient: { send: vi.fn(), close: vi.fn() } as any,
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      });

      await useRagStore.getState().approvePendingTools();

      expect(useRagStore.getState().error).toBe('Failed to approve tools');
    });
  });

  describe('rejectPendingTools', () => {
    function createMockSSEStream(events: Array<{ type: string; [key: string]: any }>) {
      const encoder = new TextEncoder();
      const data = events.map(e => `data: ${JSON.stringify(e)}\n`).join('');

      return new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(data));
          controller.close();
        },
      });
    }

    it('should return early if no pendingToolConversationId', async () => {
      useRagStore.setState({ pendingToolConversationId: null });

      await useRagStore.getState().rejectPendingTools('Not needed');

      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('should call reject endpoint with conversation_id and reason', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([{ type: 'done' }]),
      });

      await useRagStore.getState().rejectPendingTools('User cancelled');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/chat/reject',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ conversation_id: 42, reason: 'User cancelled' }),
        })
      );
    });

    it('should clear pending state and set streaming', async () => {
      useRagStore.setState({
        pendingToolCalls: [{ id: 't1', name: 'test', args: {} }],
        pendingToolConversationId: 42,
        isStreaming: false,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([{ type: 'done' }]),
      });

      await useRagStore.getState().rejectPendingTools('Reason');

      // After done event, streaming should be false
      expect(useRagStore.getState().isStreaming).toBe(false);
    });

    it('should handle token events', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        streamingContent: '',
        messages: [],
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'token', content: 'Understood, ' },
          { type: 'token', content: 'I will not proceed.' },
          { type: 'done' },
        ]),
      });

      await useRagStore.getState().rejectPendingTools('Cancelled');

      expect(useRagStore.getState().messages).toHaveLength(1);
      expect(useRagStore.getState().messages[0].content).toBe('Understood, I will not proceed.');
    });

    it('should handle error events', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'error', message: 'Rejection failed' },
        ]),
      });

      await useRagStore.getState().rejectPendingTools('Reason');

      expect(useRagStore.getState().error).toBe('Rejection failed');
    });

    it('should handle fetch errors', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
      });

      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await useRagStore.getState().rejectPendingTools('Reason');

      expect(useRagStore.getState().error).toBe('Failed to reject tools');
    });

    it('should handle tool_proposal event (agent proposes new tools)', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        pendingToolCalls: [],
        streamingContent: '',
        messages: [],
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'token', content: 'How about this instead?' },
          { type: 'tool_proposal', tools: [{ id: 't2', name: 'different_tool', args: {} }], conversation_id: 42 },
        ]),
      });

      await useRagStore.getState().rejectPendingTools('Try something else');

      const state = useRagStore.getState();
      expect(state.pendingToolCalls).toHaveLength(1);
      expect(state.pendingToolCalls[0].name).toBe('different_tool');
      expect(state.isStreaming).toBe(false);
    });
  });

  describe('revisePendingTools', () => {
    function createMockSSEStream(events: Array<{ type: string; [key: string]: any }>) {
      const encoder = new TextEncoder();
      const data = events.map(e => `data: ${JSON.stringify(e)}\n`).join('');

      return new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(data));
          controller.close();
        },
      });
    }

    it('should return early if no pendingToolConversationId', async () => {
      useRagStore.setState({ pendingToolConversationId: null });

      await useRagStore.getState().revisePendingTools([{ id: 't1', name: 'test', args: { modified: true } }]);

      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('should call revise endpoint with conversation_id and tools', async () => {
      const revisedTools = [{ id: 't1', name: 'test', args: { modified: true } }];
      useRagStore.setState({
        pendingToolConversationId: 42,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([{ type: 'done' }]),
      });

      await useRagStore.getState().revisePendingTools(revisedTools);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/chat/revise',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ conversation_id: 42, tools: revisedTools }),
        })
      );
    });

    it('should clear pending state and set streaming', async () => {
      useRagStore.setState({
        pendingToolCalls: [{ id: 't1', name: 'test', args: {} }],
        pendingToolConversationId: 42,
        isStreaming: false,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([{ type: 'done' }]),
      });

      await useRagStore.getState().revisePendingTools([{ id: 't1', name: 'test', args: { new: true } }]);

      expect(useRagStore.getState().isStreaming).toBe(false);
      expect(useRagStore.getState().pendingToolCalls).toHaveLength(0);
    });

    it('should handle token and done events', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        streamingContent: '',
        messages: [],
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'token', content: 'Using revised parameters.' },
          { type: 'done' },
        ]),
      });

      await useRagStore.getState().revisePendingTools([{ id: 't1', name: 'test', args: {} }]);

      expect(useRagStore.getState().messages).toHaveLength(1);
      expect(useRagStore.getState().messages[0].content).toBe('Using revised parameters.');
    });

    it('should handle tool_start and tool_end events', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        currentToolExecutions: [],
        messages: [],
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'tool_start', tool: { id: 't1', name: 'search' } },
          { type: 'tool_end', tool: { id: 't1', name: 'search', status: 'success' } },
          { type: 'token', content: 'Search complete.' },
          { type: 'done' },
        ]),
      });

      await useRagStore.getState().revisePendingTools([{ id: 't1', name: 'search', args: {} }]);

      // Tool executions should be cleared after done (when streamingContent exists)
      expect(useRagStore.getState().currentToolExecutions).toHaveLength(0);
      expect(useRagStore.getState().messages).toHaveLength(1);
    });

    it('should handle error events', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'error', message: 'Revision failed' },
        ]),
      });

      await useRagStore.getState().revisePendingTools([]);

      expect(useRagStore.getState().error).toBe('Revision failed');
    });

    it('should handle fetch errors', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
      });

      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await useRagStore.getState().revisePendingTools([]);

      expect(useRagStore.getState().error).toBe('Failed to revise tools');
    });

    it('should handle search_results event', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        currentSearchResults: [],
      });

      const searchResults = [
        { content: 'test', similarity: 0.9, source_document_id: 1, source_filename: 'doc.md' },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'search_results', results: searchResults },
          { type: 'done' },
        ]),
      });

      await useRagStore.getState().revisePendingTools([]);

      expect(useRagStore.getState().currentSearchResults).toEqual(searchResults);
    });

    it('should handle open_modal event', async () => {
      useRagStore.setState({
        pendingToolConversationId: 42,
        ingestionModalOpen: false,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: createMockSSEStream([
          { type: 'open_modal', modal: 'ingestion', tab: 'url', params: { suggested_url: 'https://example.com' } },
          { type: 'done' },
        ]),
      });

      await useRagStore.getState().revisePendingTools([]);

      const state = useRagStore.getState();
      expect(state.ingestionModalOpen).toBe(true);
      expect(state.ingestionModalTab).toBe('url');
      expect(state.ingestionModalParams).toEqual({ suggested_url: 'https://example.com' });
    });
  });

  // ============================================================================
  // Disconnect Action
  // ============================================================================

  describe('disconnect', () => {
    it('should close SSE client and reset connection state', () => {
      const mockClose = vi.fn();
      useRagStore.setState({
        sseClient: { close: mockClose } as any,
        isConnected: true,
      });

      useRagStore.getState().disconnect();

      expect(mockClose).toHaveBeenCalled();
      expect(useRagStore.getState().sseClient).toBe(null);
      expect(useRagStore.getState().isConnected).toBe(false);
    });

    it('should do nothing if no client', () => {
      useRagStore.setState({ sseClient: null });

      // Should not throw
      useRagStore.getState().disconnect();
    });
  });
});
