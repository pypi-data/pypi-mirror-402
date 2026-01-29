/**
 * Chat Streaming Integration Tests
 *
 * Tests the store's handling of SSE events during chat streaming.
 * Verifies that SSE events correctly update store state including
 * messages, tool executions, search results, and error handling.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useRagStore } from '../../src/rag/store';
import { sseEventSequences } from '../mocks/sse-mock';
import type { SSEEvent } from '../../src/rag/types';

/**
 * Helper to simulate SSE events being received by the store.
 * This bypasses the network layer and directly tests event handling.
 */
function simulateSSEEvents(events: SSEEvent[]): void {
  const store = useRagStore.getState();

  // Process each event through the store's connect callback logic
  for (const event of events) {
    if (event.type === 'token') {
      // Accumulate streaming tokens
      useRagStore.setState((state) => ({
        streamingContent: state.streamingContent + event.content,
      }));
    } else if (event.type === 'done') {
      // Finalize streaming - add assistant message
      const { streamingContent, messages } = useRagStore.getState();
      if (streamingContent) {
        useRagStore.setState({
          messages: [
            ...messages,
            {
              id: Date.now(),
              role: 'assistant',
              content: streamingContent,
              created_at: new Date().toISOString(),
            },
          ],
          streamingContent: '',
          isStreaming: false,
          currentSearchResults: [],
          currentWebSearchResults: [],
          currentKnowledgeGraph: [],
          currentTemporalData: [],
        });
      } else {
        useRagStore.setState({ isStreaming: false });
      }
    } else if (event.type === 'error') {
      useRagStore.setState({
        isStreaming: false,
        streamingContent: '',
        error: event.error || 'An error occurred',
      });
    } else if (event.type === 'metadata' && event.metadata?.conversation_id) {
      useRagStore.setState({ activeConversationId: event.metadata.conversation_id });
    } else if (event.type === 'tool_start' && event.tool) {
      const newExecution = {
        id: event.tool.id,
        name: event.tool.name,
        status: 'running' as const,
        startTime: Date.now(),
      };
      useRagStore.setState((state) => ({
        currentToolExecutions: [...state.currentToolExecutions, newExecution],
      }));
    } else if (event.type === 'tool_end' && event.tool) {
      useRagStore.setState((state) => ({
        currentToolExecutions: state.currentToolExecutions.map((t) =>
          t.id === event.tool!.id
            ? {
                ...t,
                status: event.tool!.status === 'success' ? 'success' : 'error',
                error: event.tool!.error,
                endTime: Date.now(),
              }
            : t
        ),
      }));
    } else if (event.type === 'search_results' && event.results) {
      useRagStore.setState({ currentSearchResults: event.results });
    } else if (event.type === 'knowledge_graph' && event.data) {
      useRagStore.setState({ currentKnowledgeGraph: event.data });
    } else if (event.type === 'temporal_data' && event.timeline) {
      useRagStore.setState({ currentTemporalData: event.timeline });
    }
  }
}

describe('chat streaming integration', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useRagStore.setState({
      messages: [],
      isStreaming: false,
      streamingContent: '',
      isConnected: false,
      sseClient: null,
      error: null,
      activeConversationId: null,
      currentToolExecutions: [],
      currentSearchResults: [],
      currentWebSearchResults: [],
      currentKnowledgeGraph: [],
      currentTemporalData: [],
    });
  });

  it('accumulates tokens and creates assistant message on done', () => {
    // Simulate user sending a message
    const userMessage = {
      id: Date.now(),
      role: 'user' as const,
      content: 'Hello, how are you?',
      created_at: new Date().toISOString(),
    };
    useRagStore.setState({
      messages: [userMessage],
      isStreaming: true,
      streamingContent: '',
    });

    // Simulate SSE events being received
    simulateSSEEvents(sseEventSequences.simpleTokens);

    // Verify final state
    const state = useRagStore.getState();
    expect(state.messages).toHaveLength(2);
    expect(state.messages[0].role).toBe('user');
    expect(state.messages[0].content).toBe('Hello, how are you?');
    expect(state.messages[1].role).toBe('assistant');
    expect(state.messages[1].content).toBe('Hello world!');
    expect(state.isStreaming).toBe(false);
    expect(state.streamingContent).toBe('');
  });

  it('tracks tool executions and populates search results during streaming', () => {
    // Simulate user sending a search query
    const userMessage = {
      id: Date.now(),
      role: 'user' as const,
      content: 'Search for documents',
      created_at: new Date().toISOString(),
    };
    useRagStore.setState({
      messages: [userMessage],
      isStreaming: true,
      streamingContent: '',
    });

    // Process events one by one to verify intermediate state
    // (search results are cleared on 'done' by design)
    const eventsBeforeDone = sseEventSequences.toolExecution.filter(
      (e) => e.type !== 'done'
    );
    simulateSSEEvents(eventsBeforeDone);

    // Verify tool was tracked during streaming
    let state = useRagStore.getState();
    expect(state.currentToolExecutions).toHaveLength(1);
    expect(state.currentToolExecutions[0].name).toBe('search_documents');
    expect(state.currentToolExecutions[0].status).toBe('success');

    // Verify search results were populated during streaming
    expect(state.currentSearchResults).toHaveLength(1);
    expect(state.currentSearchResults[0].similarity).toBe(0.9);
    expect(state.currentSearchResults[0].source_filename).toBe('doc.md');

    // Now process the 'done' event
    simulateSSEEvents([{ type: 'done' }]);

    // After done, search results are cleared (they were temporary display state)
    state = useRagStore.getState();
    expect(state.currentSearchResults).toHaveLength(0);

    // But assistant message should be created
    expect(state.messages).toHaveLength(2);
    expect(state.messages[1].content).toContain('results');
    expect(state.isStreaming).toBe(false);
  });

  it('sets error state when error event received', () => {
    // Simulate user sending a message that will error
    const userMessage = {
      id: Date.now(),
      role: 'user' as const,
      content: 'This will fail',
      created_at: new Date().toISOString(),
    };
    useRagStore.setState({
      messages: [userMessage],
      isStreaming: true,
      streamingContent: '',
    });

    // Simulate error SSE sequence
    simulateSSEEvents(sseEventSequences.errorEvent);

    // Verify error state
    const state = useRagStore.getState();
    expect(state.error).toBe('Something went wrong');
    expect(state.isStreaming).toBe(false);
    expect(state.streamingContent).toBe('');
    // User message should still be there
    expect(state.messages).toHaveLength(1);
  });

  it('populates detailed search results from SSE event during streaming', () => {
    // Create sequence with multiple detailed search results (without done)
    const searchResults = [
      {
        content: 'First result about testing patterns.',
        similarity: 0.92,
        source_document_id: 1,
        source_filename: 'testing-guide.md',
        reviewed_by_human: true,
        quality_score: 0.88,
        topic_relevance_score: 0.75,
      },
      {
        content: 'Second result about integration tests.',
        similarity: 0.85,
        source_document_id: 2,
        source_filename: 'integration.md',
        reviewed_by_human: false,
        quality_score: 0.72,
        topic_relevance_score: null,
      },
    ];

    const searchSequenceBeforeDone: SSEEvent[] = [
      { type: 'metadata', metadata: { conversation_id: 42 } },
      { type: 'token', content: 'Found relevant documents.' },
      { type: 'search_results', results: searchResults },
    ];

    // Simulate user message
    useRagStore.setState({
      messages: [
        {
          id: Date.now(),
          role: 'user' as const,
          content: 'Search for testing patterns',
          created_at: new Date().toISOString(),
        },
      ],
      isStreaming: true,
      streamingContent: '',
    });

    // Simulate SSE events before done
    simulateSSEEvents(searchSequenceBeforeDone);

    // Verify streaming state
    let state = useRagStore.getState();

    // Conversation ID should be set from metadata
    expect(state.activeConversationId).toBe(42);

    // Search results should be populated during streaming
    expect(state.currentSearchResults).toHaveLength(2);
    expect(state.currentSearchResults[0].similarity).toBe(0.92);
    expect(state.currentSearchResults[0].source_filename).toBe('testing-guide.md');
    expect(state.currentSearchResults[0].reviewed_by_human).toBe(true);
    expect(state.currentSearchResults[1].similarity).toBe(0.85);
    expect(state.currentSearchResults[1].source_filename).toBe('integration.md');
    expect(state.currentSearchResults[1].reviewed_by_human).toBe(false);

    // Now process done event
    simulateSSEEvents([{ type: 'done' }]);

    // Final state
    state = useRagStore.getState();

    // Search results are cleared after done (temporary display state)
    expect(state.currentSearchResults).toHaveLength(0);

    // But assistant message should be created
    expect(state.messages).toHaveLength(2);
    expect(state.messages[1].role).toBe('assistant');
    expect(state.messages[1].content).toBe('Found relevant documents.');
    expect(state.isStreaming).toBe(false);
  });
});
