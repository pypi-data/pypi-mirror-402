/**
 * SSE Mock Helper for testing ChatSSEClient and streaming functionality
 *
 * Provides utilities to create mock SSE streams with configurable events.
 */

import type { SSEEvent } from '../../src/rag/types';

/**
 * Creates a mock ReadableStream that emits SSE events
 */
export function createMockSSEStream(events: SSEEvent[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();

  return new ReadableStream({
    start(controller) {
      for (const event of events) {
        const data = `data: ${JSON.stringify(event)}\n\n`;
        controller.enqueue(encoder.encode(data));
      }
      controller.close();
    },
  });
}

/**
 * Creates a mock ReadableStream with delayed events (for testing streaming behavior)
 */
export function createDelayedSSEStream(
  events: SSEEvent[],
  delayMs: number = 10
): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();

  return new ReadableStream({
    async start(controller) {
      for (const event of events) {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
        const data = `data: ${JSON.stringify(event)}\n\n`;
        controller.enqueue(encoder.encode(data));
      }
      controller.close();
    },
  });
}

/**
 * Creates a mock fetch Response with SSE stream
 */
export function createMockSSEResponse(events: SSEEvent[]): Response {
  const stream = createMockSSEStream(events);
  return new Response(stream, {
    headers: { 'Content-Type': 'text/event-stream' },
  });
}

/**
 * Common SSE event sequences for testing
 */
export const sseEventSequences = {
  // Simple token streaming
  simpleTokens: [
    { type: 'metadata', metadata: { conversation_id: 1 } },
    { type: 'token', content: 'Hello' },
    { type: 'token', content: ' world' },
    { type: 'token', content: '!' },
    { type: 'done' },
  ] as SSEEvent[],

  // Tool execution flow
  toolExecution: [
    { type: 'metadata', metadata: { conversation_id: 1 } },
    { type: 'token', content: 'Let me search for that.' },
    { type: 'tool_start', tool: { id: 'tool-1', name: 'search_documents' } },
    { type: 'tool_end', tool: { id: 'tool-1', name: 'search_documents', status: 'success' } },
    { type: 'search_results', results: [{ content: 'Result 1', similarity: 0.9, source_document_id: 1, source_filename: 'doc.md', reviewed_by_human: false, quality_score: 0.8, topic_relevance_score: null }] },
    { type: 'token', content: 'Here are the results.' },
    { type: 'done' },
  ] as SSEEvent[],

  // Tool proposal (needs approval)
  toolProposal: [
    { type: 'metadata', metadata: { conversation_id: 1 } },
    { type: 'token', content: 'I need to create a collection.' },
    {
      type: 'tool_proposal',
      tools: [
        { id: 'tool-1', name: 'create_collection', args: { name: 'test', description: 'Test collection' } },
      ],
      conversation_id: 1,
    },
  ] as SSEEvent[],

  // Error event
  errorEvent: [
    { type: 'metadata', metadata: { conversation_id: 1 } },
    { type: 'error', error: 'Something went wrong' },
  ] as SSEEvent[],

  // Knowledge graph query
  knowledgeGraphQuery: [
    { type: 'metadata', metadata: { conversation_id: 1 } },
    { type: 'token', content: 'Querying relationships...' },
    { type: 'tool_start', tool: { id: 'tool-1', name: 'query_relationships' } },
    { type: 'tool_end', tool: { id: 'tool-1', name: 'query_relationships', status: 'success' } },
    {
      type: 'knowledge_graph',
      data: [
        { id: 'rel-1', relationship_type: 'relates_to', fact: 'A relates to B', source_node_id: 'a', target_node_id: 'b' },
      ],
    },
    { type: 'token', content: 'Found relationships.' },
    { type: 'done' },
  ] as SSEEvent[],

  // Temporal query
  temporalQuery: [
    { type: 'metadata', metadata: { conversation_id: 1 } },
    { type: 'token', content: 'Checking timeline...' },
    { type: 'tool_start', tool: { id: 'tool-1', name: 'query_temporal' } },
    { type: 'tool_end', tool: { id: 'tool-1', name: 'query_temporal', status: 'success' } },
    {
      type: 'temporal_data',
      timeline: [
        { fact: 'Feature added', relationship_type: 'added', valid_from: '2024-01-01', valid_until: null, status: 'current', created_at: '2024-01-01T00:00:00Z' },
      ],
    },
    { type: 'token', content: 'Timeline retrieved.' },
    { type: 'done' },
  ] as SSEEvent[],

  // Web search results
  webSearchResults: [
    { type: 'metadata', metadata: { conversation_id: 1 } },
    { type: 'token', content: 'Searching the web...' },
    { type: 'tool_start', tool: { id: 'tool-1', name: 'web_search' } },
    { type: 'tool_end', tool: { id: 'tool-1', name: 'web_search', status: 'success' } },
    {
      type: 'web_search_results',
      results: [
        { title: 'Example Result', url: 'https://example.com', snippet: 'This is an example.' },
      ],
    },
    { type: 'token', content: 'Found web results.' },
    { type: 'done' },
  ] as SSEEvent[],

  // Open modal event
  openIngestionModal: [
    { type: 'metadata', metadata: { conversation_id: 1 } },
    { type: 'token', content: 'Opening the file upload dialog...' },
    { type: 'open_modal', modal: 'ingestion', tab: 'file', params: { suggested_collection: 'docs' } },
    { type: 'done' },
  ] as SSEEvent[],

  // Multiple tool executions
  multipleTools: [
    { type: 'metadata', metadata: { conversation_id: 1 } },
    { type: 'tool_start', tool: { id: 'tool-1', name: 'list_collections' } },
    { type: 'tool_start', tool: { id: 'tool-2', name: 'search_documents' } },
    { type: 'tool_end', tool: { id: 'tool-1', name: 'list_collections', status: 'success' } },
    { type: 'tool_end', tool: { id: 'tool-2', name: 'search_documents', status: 'success' } },
    { type: 'token', content: 'Both operations complete.' },
    { type: 'done' },
  ] as SSEEvent[],

  // Tool error
  toolError: [
    { type: 'metadata', metadata: { conversation_id: 1 } },
    { type: 'tool_start', tool: { id: 'tool-1', name: 'search_documents' } },
    { type: 'tool_end', tool: { id: 'tool-1', name: 'search_documents', status: 'error', error: 'Connection failed' } },
    { type: 'token', content: 'The search failed.' },
    { type: 'done' },
  ] as SSEEvent[],
};

/**
 * Parses raw SSE text into events (useful for testing SSE parsing logic)
 */
export function parseSSEText(text: string): SSEEvent[] {
  const events: SSEEvent[] = [];
  const lines = text.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      try {
        const data = line.slice(6);
        events.push(JSON.parse(data));
      } catch {
        // Skip malformed lines
      }
    }
  }

  return events;
}

/**
 * Creates SSE text from events (for testing parsing)
 */
export function createSSEText(events: SSEEvent[]): string {
  return events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join('');
}
