import { http, HttpResponse } from 'msw';

// Base URLs for API requests
const API_BASE = 'http://localhost:8000';
const MCP_BASE = 'http://localhost:3001'; // MCP server for direct calls

// Mock data
export const mockCollections = [
  {
    id: 1,
    name: 'test-collection',
    description: 'A test collection for unit tests',
    document_count: 5,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'docs-collection',
    description: 'Documentation collection',
    document_count: 10,
    created_at: '2024-01-02T00:00:00Z',
  },
];

export const mockDocuments = [
  {
    id: 1,
    filename: 'test-doc.md',
    chunk_count: 3,
  },
  {
    id: 2,
    filename: 'another-doc.txt',
    chunk_count: 5,
  },
];

export const mockSearchResults = [
  {
    content: 'This is a test search result with relevant content.',
    similarity: 0.85,
    source_document_id: 1,
    source_filename: 'test-doc.md',
    reviewed_by_human: false,
    quality_score: 0.75,
    topic_relevance_score: null,
  },
];

export const mockConversations = [
  {
    id: 1,
    title: 'Test Conversation',
    created_at: '2024-01-01T10:00:00Z',
    updated_at: '2024-01-01T10:30:00Z',
    is_pinned: false,
  },
];

// Request handlers
export const handlers = [
  // Collections
  http.get(`${API_BASE}/api/rag-memory/collections`, () => {
    return HttpResponse.json({ collections: mockCollections });
  }),

  http.get(`${API_BASE}/api/rag-memory/collections/:name`, ({ params }) => {
    const collection = mockCollections.find((c) => c.name === params.name);
    if (!collection) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json({
      ...collection,
      chunk_count: 15,
      sample_documents: mockDocuments.slice(0, 2),
      crawled_urls: [],
    });
  }),

  http.get(`${API_BASE}/api/rag-memory/collections/:name/schema`, ({ params }) => {
    const collection = mockCollections.find((c) => c.name === params.name);
    if (!collection) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json({
      collection_name: collection.name,
      description: collection.description,
      document_count: collection.document_count,
      metadata_schema: {
        mandatory: { domain: 'string', domain_scope: 'string' },
        custom: {},
        system: ['created_at', 'updated_at'],
      },
      custom_fields: {},
      system_fields: ['created_at', 'updated_at'],
    });
  }),

  http.post(`${API_BASE}/api/rag-memory/collections`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({
      collection_id: 3,
      name: body.name,
      description: body.description,
      created: true,
    });
  }),

  http.delete(`${API_BASE}/api/rag-memory/collections/:name`, () => {
    return HttpResponse.json({ deleted: true });
  }),

  // Documents
  http.get(`${API_BASE}/api/rag-memory/documents`, () => {
    return HttpResponse.json({ documents: mockDocuments });
  }),

  http.get(`${API_BASE}/api/rag-memory/documents/:id`, ({ params }) => {
    const doc = mockDocuments.find((d) => d.id === Number(params.id));
    if (!doc) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json({
      ...doc,
      content: 'Full document content here',
      file_type: 'text/markdown',
      file_size: 1024,
      metadata: {},
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      collections: ['test-collection'],
    });
  }),

  http.delete(`${API_BASE}/api/rag-memory/documents/:id`, () => {
    return HttpResponse.json({ deleted: true });
  }),

  // Search
  http.post(`${API_BASE}/api/rag-memory/search`, () => {
    return HttpResponse.json({ results: mockSearchResults });
  }),

  // Knowledge Graph
  http.post(`${API_BASE}/api/rag-memory/graph/relationships`, () => {
    return HttpResponse.json({
      status: 'success',
      relationships: [
        {
          id: 'rel-1',
          relationship_type: 'relates_to',
          fact: 'Test relates to Documentation',
          source_node_id: 'node-1',
          target_node_id: 'node-2',
        },
      ],
    });
  }),

  http.post(`${API_BASE}/api/rag-memory/graph/temporal`, () => {
    return HttpResponse.json({
      status: 'success',
      timeline: [
        {
          fact: 'Feature was added',
          relationship_type: 'added',
          valid_from: '2024-01-01',
          valid_until: null,
          status: 'current',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    });
  }),

  // Conversations
  http.get(`${API_BASE}/api/conversations`, () => {
    return HttpResponse.json(mockConversations);
  }),

  http.get(`${API_BASE}/api/conversations/:id`, ({ params }) => {
    const conv = mockConversations.find((c) => c.id === Number(params.id));
    if (!conv) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(conv);
  }),

  http.get(`${API_BASE}/api/conversations/:id/messages`, () => {
    return HttpResponse.json([
      {
        id: 1,
        role: 'user',
        content: 'Hello',
        created_at: '2024-01-01T10:00:00Z',
      },
      {
        id: 2,
        role: 'assistant',
        content: 'Hi there! How can I help you?',
        created_at: '2024-01-01T10:00:05Z',
      },
    ]);
  }),

  http.delete(`${API_BASE}/api/conversations/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Starter Prompts
  http.get(`${API_BASE}/api/starter-prompts`, () => {
    return HttpResponse.json([
      {
        id: 1,
        title: 'Search Documents',
        prompt: 'Search for documents about...',
        icon: 'search',
      },
    ]);
  }),

  // Conversation Management (additional endpoints)
  http.post(`${API_BASE}/api/conversations`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({
      id: 99,
      title: body.title || 'New Conversation',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      is_pinned: false,
    });
  }),

  http.patch(`${API_BASE}/api/conversations/:id`, async ({ params, request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    const conv = mockConversations.find((c) => c.id === Number(params.id));
    return HttpResponse.json({
      ...conv,
      ...body,
      updated_at: new Date().toISOString(),
    });
  }),

  http.post(`${API_BASE}/api/conversations/bulk-delete`, async () => {
    return HttpResponse.json({ deleted_count: 2 });
  }),

  http.delete(`${API_BASE}/api/conversations/all`, () => {
    return HttpResponse.json({ deleted_count: mockConversations.length });
  }),

  // Chat Endpoints (Tool approval flow)
  http.post(`${API_BASE}/api/chat/approve`, () => {
    // Return SSE stream for approval
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: {"type":"tool_start","tool":{"id":"t1","name":"search_documents"}}\n\n'));
        controller.enqueue(encoder.encode('data: {"type":"tool_end","tool":{"id":"t1","name":"search_documents","status":"success"}}\n\n'));
        controller.enqueue(encoder.encode('data: {"type":"token","content":"Here are the results"}\n\n'));
        controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
        controller.close();
      },
    });
    return new HttpResponse(stream, {
      headers: { 'Content-Type': 'text/event-stream' },
    });
  }),

  http.post(`${API_BASE}/api/chat/reject`, () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: {"type":"token","content":"I understand. Let me try a different approach."}\n\n'));
        controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
        controller.close();
      },
    });
    return new HttpResponse(stream, {
      headers: { 'Content-Type': 'text/event-stream' },
    });
  }),

  http.post(`${API_BASE}/api/chat/revise`, () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: {"type":"tool_start","tool":{"id":"t2","name":"search_documents"}}\n\n'));
        controller.enqueue(encoder.encode('data: {"type":"tool_end","tool":{"id":"t2","name":"search_documents","status":"success"}}\n\n'));
        controller.enqueue(encoder.encode('data: {"type":"token","content":"Using the revised parameters..."}\n\n'));
        controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
        controller.close();
      },
    });
    return new HttpResponse(stream, {
      headers: { 'Content-Type': 'text/event-stream' },
    });
  }),

  http.post(`${API_BASE}/api/chat/stream`, () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: {"type":"metadata","metadata":{"conversation_id":1}}\n\n'));
        controller.enqueue(encoder.encode('data: {"type":"token","content":"Hello"}\n\n'));
        controller.enqueue(encoder.encode('data: {"type":"token","content":" there!"}\n\n'));
        controller.enqueue(encoder.encode('data: {"type":"done"}\n\n'));
        controller.close();
      },
    });
    return new HttpResponse(stream, {
      headers: { 'Content-Type': 'text/event-stream' },
    });
  }),

  // MCP Server Direct Endpoints (Admin Dashboard)
  http.get(`${MCP_BASE}/api/admin/stats`, ({ request }) => {
    const url = new URL(request.url);
    const collection = url.searchParams.get('collection');
    return HttpResponse.json({
      collections: { total: collection ? 1 : 2 },
      documents: { total: 15, reviewed: 5, unreviewed: 10 },
      chunks: { total: 45 },
      quality: {
        avg: 0.72,
        min: 0.45,
        max: 0.95,
        distribution: { high: 5, medium: 7, low: 2, unscored: 1 },
      },
      topic_relevance: {
        with_topic: 10,
        without_topic: 5,
        avg_relevance: 0.68,
      },
    });
  }),

  http.get(`${MCP_BASE}/api/admin/analytics/quality`, () => {
    return HttpResponse.json({
      quality_histogram: [
        { range: '0.0-0.2', count: 1 },
        { range: '0.2-0.4', count: 2 },
        { range: '0.4-0.6', count: 4 },
        { range: '0.6-0.8', count: 5 },
        { range: '0.8-1.0', count: 3 },
      ],
      topic_histogram: [
        { range: '0.0-0.2', count: 0 },
        { range: '0.2-0.4', count: 1 },
        { range: '0.4-0.6', count: 3 },
        { range: '0.6-0.8', count: 4 },
        { range: '0.8-1.0', count: 2 },
      ],
      review_breakdown: { reviewed: 5, unreviewed: 10 },
      quality_by_collection: [
        { collection: 'test-collection', avg: 0.75, min: 0.5, max: 0.95, doc_count: 5 },
        { collection: 'docs-collection', avg: 0.68, min: 0.45, max: 0.88, doc_count: 10 },
      ],
    });
  }),

  http.get(`${MCP_BASE}/api/admin/analytics/content`, () => {
    return HttpResponse.json({
      file_type_distribution: [
        { type: 'text/markdown', count: 8, size_bytes: 50000, pct: 53.3 },
        { type: 'text/plain', count: 7, size_bytes: 35000, pct: 46.7 },
      ],
      ingest_method_breakdown: [
        { method: 'url', count: 10, pct: 66.7 },
        { method: 'file', count: 5, pct: 33.3 },
      ],
      actor_type_breakdown: [
        { actor: 'agent', count: 12, pct: 80.0 },
        { actor: 'user', count: 3, pct: 20.0 },
      ],
      ingestion_timeline: [
        { date: '2024-01-01', total: 5, url: 3, file: 2, text: 0, directory: 0 },
        { date: '2024-01-02', total: 10, url: 7, file: 3, text: 0, directory: 0 },
      ],
      crawl_stats: {
        domains: [{ domain: 'example.com', page_count: 10, avg_quality: 0.75 }],
        depth_distribution: [{ depth: 1, count: 5, label: 'Level 1' }],
        total_crawl_sessions: 3,
      },
      storage: {
        total_bytes: 85000,
        total_human: '83.0 KB',
        avg_per_doc: 5666,
        avg_human: '5.5 KB',
      },
      chunks: { total: 45, avg_per_doc: 3, min_per_doc: 1, max_per_doc: 8 },
    });
  }),

  // MCP Server: Document Review
  http.patch(`${MCP_BASE}/api/documents/review`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({
      document_id: body.document_id,
      updated_fields: ['reviewed_by_human'],
      reviewed_by_human: body.reviewed_by_human,
    });
  }),

  // MCP Server: Collection Link Management
  http.post(`${MCP_BASE}/api/documents/manage-collection-link`, async ({ request }) => {
    const formData = await request.text();
    const params = new URLSearchParams(formData);
    const unlink = params.get('unlink') === 'true';
    return HttpResponse.json({
      document_id: Number(params.get('document_id')),
      document_title: 'test-doc.md',
      collection_name: params.get('collection_name'),
      ...(unlink
        ? { chunks_unlinked: 3, status: 'unlinked', remaining_collections: ['other-collection'] }
        : { chunks_linked: 3, status: 'linked' }),
      message: unlink ? 'Document unlinked successfully' : 'Document linked successfully',
    });
  }),
];
