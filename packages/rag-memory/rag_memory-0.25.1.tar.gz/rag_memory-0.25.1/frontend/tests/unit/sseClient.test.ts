/**
 * ChatSSEClient Unit Tests
 *
 * Tests the SSE streaming client for chat functionality.
 * Tests the client in isolation by mocking fetch directly (bypassing MSW).
 */

import { describe, it, expect, vi, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';
import { ChatSSEClient } from '../../src/rag/api';
import type { SSEEvent } from '../../src/rag/types';
import { createSSEText, sseEventSequences } from '../mocks/sse-mock';
import { server } from '../mocks/server';

// Disable MSW for these tests - we're testing the client in isolation
beforeAll(() => {
  server.close();
});

afterAll(() => {
  server.listen();
});

// Store original fetch
const originalFetch = global.fetch;

// Mock fetch for SSE streaming
const mockFetch = vi.fn();

describe('ChatSSEClient', () => {
  let client: ChatSSEClient;
  let mockGetToken: () => Promise<string | null>;
  let receivedEvents: SSEEvent[];
  let onOpenCalled: boolean;
  let onCloseCalled: boolean;
  let lastError: Error | null;

  beforeEach(() => {
    // Replace global fetch with our mock
    global.fetch = mockFetch as unknown as typeof fetch;
    mockFetch.mockReset();

    mockGetToken = vi.fn().mockResolvedValue('test-token');
    receivedEvents = [];
    onOpenCalled = false;
    onCloseCalled = false;
    lastError = null;

    client = new ChatSSEClient('http://localhost:8000', mockGetToken, {
      onOpen: () => {
        onOpenCalled = true;
      },
      onClose: () => {
        onCloseCalled = true;
      },
      onMessage: (event) => {
        receivedEvents.push(event);
      },
      onError: (error) => {
        lastError = error;
      },
    });
  });

  afterEach(() => {
    client.close();
    // Restore original fetch
    global.fetch = originalFetch;
  });

  describe('constructor', () => {
    it('should initialize with correct base URL', () => {
      expect(client).toBeDefined();
      expect(client.getIsOpen()).toBe(false);
    });

    it('should accept options with callbacks', () => {
      const customClient = new ChatSSEClient(
        'http://example.com',
        mockGetToken,
        {
          onOpen: () => {},
          onClose: () => {},
          onMessage: () => {},
          onError: () => {},
        }
      );
      expect(customClient).toBeDefined();
    });
  });

  describe('send', () => {
    it('should send request with correct headers and body', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send(JSON.stringify({ message: 'test', conversation_id: 1 }));

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/chat/stream',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer test-token',
          },
          body: JSON.stringify({ message: 'test', conversation_id: 1 }),
        })
      );
    });

    it('should call onOpen when connection is established', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      expect(onOpenCalled).toBe(true);
    });

    it('should parse and emit token events', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: {"type":"token","content":"Hello"}\n\n'));
          controller.enqueue(encoder.encode('data: {"type":"token","content":" world"}\n\n'));
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      expect(receivedEvents).toHaveLength(3);
      expect(receivedEvents[0]).toEqual({ type: 'token', content: 'Hello' });
      expect(receivedEvents[1]).toEqual({ type: 'token', content: ' world' });
      expect(receivedEvents[2]).toEqual({ type: 'done' });
    });

    it('should handle tool_start and tool_end events', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: {"type":"tool_start","tool":{"id":"t1","name":"search"}}\n\n'));
          controller.enqueue(encoder.encode('data: {"type":"tool_end","tool":{"id":"t1","name":"search","status":"success"}}\n\n'));
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      const toolStart = receivedEvents.find((e) => e.type === 'tool_start');
      const toolEnd = receivedEvents.find((e) => e.type === 'tool_end');

      expect(toolStart).toBeDefined();
      expect(toolStart?.tool?.id).toBe('t1');
      expect(toolStart?.tool?.name).toBe('search');

      expect(toolEnd).toBeDefined();
      expect(toolEnd?.tool?.status).toBe('success');
    });

    it('should handle search_results events', async () => {
      const encoder = new TextEncoder();
      const results = [{ content: 'test', similarity: 0.9, source_document_id: 1, source_filename: 'doc.md', reviewed_by_human: false, quality_score: 0.8, topic_relevance_score: null }];
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(`data: {"type":"search_results","results":${JSON.stringify(results)}}\n\n`));
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      const searchEvent = receivedEvents.find((e) => e.type === 'search_results');
      expect(searchEvent).toBeDefined();
      expect(searchEvent?.results).toEqual(results);
    });

    it('should handle tool_proposal events', async () => {
      const encoder = new TextEncoder();
      const tools = [{ id: 't1', name: 'create_collection', args: { name: 'test' } }];
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(`data: {"type":"tool_proposal","tools":${JSON.stringify(tools)},"conversation_id":1}\n\n`));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      const proposalEvent = receivedEvents.find((e) => e.type === 'tool_proposal');
      expect(proposalEvent).toBeDefined();
      expect(proposalEvent?.tools).toEqual(tools);
      expect(proposalEvent?.conversation_id).toBe(1);
    });

    it('should handle error events', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: {"type":"error","error":"Something went wrong"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      const errorEvent = receivedEvents.find((e) => e.type === 'error');
      expect(errorEvent).toBeDefined();
      expect(errorEvent?.error).toBe('Something went wrong');
    });

    it('should handle HTTP errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await client.send('{}');

      expect(lastError?.message).toContain('HTTP error');
      // Error should also be sent as an event
      const errorEvent = receivedEvents.find((e) => e.type === 'error');
      expect(errorEvent).toBeDefined();
    });

    it('should handle null response body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: null,
      });

      await client.send('{}');

      expect(lastError?.message).toBe('Response body is null');
    });

    it('should handle partial SSE lines (line buffering)', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          // Simulate partial data arriving in chunks
          controller.enqueue(encoder.encode('data: {"type":"tok'));
          controller.enqueue(encoder.encode('en","content":"Hello"}\n\n'));
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      expect(receivedEvents).toHaveLength(2);
      expect(receivedEvents[0]).toEqual({ type: 'token', content: 'Hello' });
    });

    it('should skip malformed JSON data gracefully', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: not valid json\n\n'));
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      // Should not throw
      await client.send('{}');

      // Only the valid event should be received
      expect(receivedEvents).toHaveLength(1);
      expect(receivedEvents[0].type).toBe('done');
    });

    it('should abort previous request when sending new message', async () => {
      const abortController = new AbortController();
      let requestCount = 0;

      mockFetch.mockImplementation((_url: string, options: RequestInit) => {
        requestCount++;
        const signal = options.signal as AbortSignal;

        return new Promise((resolve, reject) => {
          signal.addEventListener('abort', () => {
            reject(new DOMException('Aborted', 'AbortError'));
          });

          // Only complete if not aborted
          if (!signal.aborted) {
            const encoder = new TextEncoder();
            const stream = new ReadableStream({
              start(controller) {
                controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
                controller.close();
              },
            });

            setTimeout(() => {
              if (!signal.aborted) {
                resolve({ ok: true, body: stream });
              }
            }, 50);
          }
        });
      });

      // Start first request
      const firstRequest = client.send('{"message":"first"}');

      // Immediately send second request (should abort first)
      const secondRequest = client.send('{"message":"second"}');

      await Promise.all([firstRequest, secondRequest].map((p) => p.catch(() => {})));

      // Both requests should have been made
      expect(requestCount).toBe(2);
    });

    it('should not send Authorization header when no token', async () => {
      const noTokenClient = new ChatSSEClient(
        'http://localhost:8000',
        () => Promise.resolve(null),
        {}
      );

      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await noTokenClient.send('{}');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
    });
  });

  describe('close', () => {
    it('should abort ongoing request', async () => {
      let aborted = false;

      mockFetch.mockImplementation((_url: string, options: RequestInit) => {
        const signal = options.signal as AbortSignal;
        return new Promise((resolve, reject) => {
          signal.addEventListener('abort', () => {
            aborted = true;
            reject(new DOMException('Aborted', 'AbortError'));
          });

          // Never resolve to simulate long-running request
        });
      });

      // Start request without awaiting
      client.send('{}');

      // Give it a moment to start
      await new Promise((r) => setTimeout(r, 10));

      // Close should abort
      client.close();

      expect(aborted).toBe(true);
    });

    it('should call onClose callback when open', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          // Don't close immediately - simulate open connection
          setTimeout(() => {
            controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
            controller.close();
          }, 100);
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      // Start request
      const promise = client.send('{}');

      // Wait for connection to open
      await new Promise((r) => setTimeout(r, 20));

      expect(onOpenCalled).toBe(true);

      // Close while still streaming
      client.close();

      expect(onCloseCalled).toBe(true);

      // Clean up
      await promise.catch(() => {});
    });

    it('should set isOpen to false', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      client.close();

      expect(client.getIsOpen()).toBe(false);
    });
  });

  describe('getIsOpen', () => {
    it('should return false initially', () => {
      expect(client.getIsOpen()).toBe(false);
    });

    it('should return true during active stream', async () => {
      let isOpenDuringStream = false;

      const customClient = new ChatSSEClient('http://localhost:8000', mockGetToken, {
        onMessage: () => {
          isOpenDuringStream = customClient.getIsOpen();
        },
      });

      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: {"type":"token","content":"test"}\n\n'));
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await customClient.send('{}');

      expect(isOpenDuringStream).toBe(true);
    });

    it('should return false after stream completes', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      expect(client.getIsOpen()).toBe(false);
    });
  });

  describe('metadata event handling', () => {
    it('should emit metadata event with conversation_id', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: {"type":"metadata","metadata":{"conversation_id":42}}\n\n'));
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      const metadataEvent = receivedEvents.find((e) => e.type === 'metadata');
      expect(metadataEvent).toBeDefined();
      expect(metadataEvent?.metadata?.conversation_id).toBe(42);
    });
  });

  describe('knowledge graph and temporal events', () => {
    it('should emit knowledge_graph event', async () => {
      const encoder = new TextEncoder();
      const graphData = [{ id: 'rel-1', fact: 'A relates to B' }];
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(`data: {"type":"knowledge_graph","data":${JSON.stringify(graphData)}}\n\n`));
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      const graphEvent = receivedEvents.find((e) => e.type === 'knowledge_graph');
      expect(graphEvent).toBeDefined();
      expect(graphEvent?.data).toEqual(graphData);
    });

    it('should emit temporal_data event', async () => {
      const encoder = new TextEncoder();
      const timeline = [{ fact: 'Feature added', valid_from: '2024-01-01' }];
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(`data: {"type":"temporal_data","timeline":${JSON.stringify(timeline)}}\n\n`));
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      const temporalEvent = receivedEvents.find((e) => e.type === 'temporal_data');
      expect(temporalEvent).toBeDefined();
      expect(temporalEvent?.timeline).toEqual(timeline);
    });
  });

  describe('open_modal event', () => {
    it('should emit open_modal event with tab and params', async () => {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode('data: {"type":"open_modal","modal":"ingestion","tab":"url","params":{"suggested_url":"https://example.com"}}\n\n'));
          controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
          controller.close();
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: stream,
      });

      await client.send('{}');

      const modalEvent = receivedEvents.find((e) => e.type === 'open_modal');
      expect(modalEvent).toBeDefined();
      expect(modalEvent?.modal).toBe('ingestion');
      expect(modalEvent?.tab).toBe('url');
      expect(modalEvent?.params).toEqual({ suggested_url: 'https://example.com' });
    });
  });
});
