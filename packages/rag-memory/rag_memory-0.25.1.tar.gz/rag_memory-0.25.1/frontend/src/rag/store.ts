/**
 * Zustand store for RAG Memory Web state management
 *
 * Following Lumentor pattern from agent-architecture-platform
 */

import { create } from 'zustand';
import type {
  RagState,
  ChatMessage,
  SearchResult,
  WebSearchResult,
} from './types';
import { ChatSSEClient } from './api';
import * as ragApi from './ragApi';

export const useRagStore = create<RagState>((set, get) => ({
  // ============================================================================
  // Chat State
  // ============================================================================
  messages: [],
  conversations: [],
  isConnected: false,
  isStreaming: false,
  streamingContent: '',
  sseClient: null,
  activeConversationId: null,
  currentToolExecutions: [],
  error: null,
  inputValue: '',

  // ============================================================================
  // RAG State
  // ============================================================================
  collections: [],
  selectedCollectionId: null,
  documents: [],
  selectedDocumentId: null,
  searchResults: [],
  knowledgeGraphData: [],

  // Rich content from streaming events
  currentSearchResults: [],
  currentWebSearchResults: [],
  currentKnowledgeGraph: [],
  currentTemporalData: [],

  // Tool approval state
  pendingToolCalls: [],
  pendingToolConversationId: null,

  // Agent-triggered modal state
  ingestionModalOpen: false,
  ingestionModalTab: 'file' as const,
  ingestionModalParams: {},

  // ============================================================================
  // Actions
  // ============================================================================

  connect: async (getToken) => {
    const sseClient = new ChatSSEClient(
      import.meta.env.VITE_API_URL || 'http://localhost:8000',
      getToken,
      {
        onOpen: () => set({ isConnected: true }),
        onClose: () => set({ isConnected: false, sseClient: null }),
        onMessage: (event) => {
          if (event.type === 'token') {
            // Accumulate streaming tokens
            set((state) => ({
              streamingContent: state.streamingContent + event.content,
            }));
          } else if (event.type === 'done') {
            // Finalize streaming - add assistant message
            const { streamingContent, messages } = get();
            if (streamingContent) {
              set({
                messages: [
                  ...messages,
                  {
                    id: Date.now(), // Temporary ID
                    role: 'assistant',
                    content: streamingContent,
                    created_at: new Date().toISOString(),
                  },
                ],
                streamingContent: '',
                isStreaming: false,
                // Clear rich content for next message
                currentSearchResults: [],
                currentWebSearchResults: [],
                currentKnowledgeGraph: [],
                currentTemporalData: [],
              });

              // Clear tool executions after a delay so user can see "completed" status
              setTimeout(() => {
                set({ currentToolExecutions: [] });
              }, 1500); // 1.5 seconds - enough time to see completion
            }
          } else if (event.type === 'error') {
            console.error('WebSocket error:', event.error);
            set({
              isStreaming: false,
              streamingContent: '',
              error: event.error || 'An error occurred',
            });
          } else if (event.type === 'metadata' && event.metadata?.conversation_id) {
            set({ activeConversationId: event.metadata.conversation_id });
          } else if (event.type === 'tool_start' && event.tool) {
            // Track tool execution start
            const newExecution = {
              id: event.tool.id,
              name: event.tool.name,
              status: 'running' as const,
              startTime: Date.now(),
            };
            set((state) => ({
              currentToolExecutions: [...state.currentToolExecutions, newExecution],
            }));
          } else if (event.type === 'tool_end' && event.tool) {
            // Update tool execution status
            set((state) => ({
              currentToolExecutions: state.currentToolExecutions.map((exec) =>
                exec.id === event.tool!.id
                  ? {
                      ...exec,
                      status: event.tool!.status === 'error' ? 'failed' : 'completed',
                      endTime: Date.now(),
                      error: event.tool!.error,
                    }
                  : exec
              ),
            }));

            // Refresh collections if create_collection completed successfully
            if (event.tool.name === 'create_collection' && event.tool.status !== 'error') {
              get().loadCollections();
            }
          } else if (event.type === 'search_results') {
            // Ensure results is always an array
            const results = Array.isArray(event.results) ? event.results : [];
            // Type assertion: search_results should always contain SearchResult[]
            set({ currentSearchResults: results as SearchResult[] });
          } else if (event.type === 'web_search_results' && event.results) {
            // Store web search results for rendering
            set({ currentWebSearchResults: event.results as WebSearchResult[] });
          } else if (event.type === 'knowledge_graph' && event.data) {
            // Store knowledge graph data for rendering
            set({ currentKnowledgeGraph: event.data });
          } else if (event.type === 'temporal_data' && event.timeline) {
            // Store temporal data for rendering
            set({ currentTemporalData: event.timeline });
          } else if (event.type === 'open_modal' && event.modal === 'ingestion') {
            // Agent requested to open the ingestion modal with pre-filled params
            console.log('Open modal event received:', event);
            const tab = event.tab || 'file';
            const params = event.params || {};
            set({
              ingestionModalOpen: true,
              ingestionModalTab: tab,
              ingestionModalParams: params,
            });
          } else if (event.type === 'tool_proposal' && event.tools) {
            // Agent wants to execute tools - store for user approval
            console.log('Tool proposal received:', event.tools);

            // First finalize any streamed content as assistant message
            const { streamingContent, messages } = get();
            if (streamingContent) {
              set({
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
              });
            }

            // Store pending tools for approval UI
            set({
              pendingToolCalls: event.tools,
              pendingToolConversationId: event.conversation_id || get().activeConversationId,
              isStreaming: false, // Stop streaming indicator - waiting for user
            });
          }
          // TODO: Add 'document_selected' to SSEEventType and document_id to SSEEvent
          // to support automatic document viewer opening
          // } else if (event.type === 'document_selected' && event.document_id) {
          //   set({ selectedDocumentId: event.document_id });
          // }
        },
      }
    );

    set({ sseClient });
  },

  disconnect: () => {
    const { sseClient } = get();
    if (sseClient) {
      sseClient.close();
      set({ sseClient: null, isConnected: false });
    }
  },

  sendMessage: async (content) => {
    const { sseClient, activeConversationId, messages } = get();

    // Auto-create conversation if none active (Lumentor pattern)
    let conversationId = activeConversationId;
    if (!conversationId) {
      // Create conversation on frontend first
      const title = content.length > 50 ? content.substring(0, 50) + '...' : content;
      try {
        const response = await fetch('http://localhost:8000/api/conversations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title }),
        });
        const conversation = await response.json();
        conversationId = conversation.id;
        set({ activeConversationId: conversationId });
      } catch (error) {
        console.error('Failed to create conversation:', error);
        set({ error: 'Failed to create conversation' });
        return;
      }
    }

    // Add user message optimistically
    const userMessage: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    set({
      messages: [...messages, userMessage],
      isStreaming: true,
      streamingContent: '',
    });

    if (sseClient) {
      sseClient.send(JSON.stringify({
        message: content,
        conversation_id: conversationId,  // ALWAYS send conversation_id
      }));
    }
  },

  // ============================================================================
  // Conversation Management
  // ============================================================================

  loadConversations: async () => {
    try {
      const response = await fetch('http://localhost:8000/api/conversations');
      const conversations = await response.json();
      // Sort by updated_at descending (most recent first)
      conversations.sort((a: any, b: any) =>
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      );
      set({ conversations });
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  },

  selectConversation: async (conversationId) => {
    try {
      // Load messages for this conversation
      const response = await fetch(`http://localhost:8000/api/conversations/${conversationId}/messages`);
      const messages = await response.json();

      set({
        activeConversationId: conversationId,
        messages,
        // Clear any streaming state when switching conversations
        isStreaming: false,
        streamingContent: '',
        currentToolExecutions: [],
        // Clear rich content
        currentSearchResults: [],
        currentWebSearchResults: [],
        currentKnowledgeGraph: [],
        currentTemporalData: [],
      });
    } catch (error) {
      console.error('Failed to load conversation:', error);
      set({ error: 'Failed to load conversation' });
    }
  },

  deleteConversation: async (conversationId) => {
    try {
      await fetch(`http://localhost:8000/api/conversations/${conversationId}`, {
        method: 'DELETE',
      });

      // Remove from conversations list
      set((state) => ({
        conversations: state.conversations.filter((c) => c.id !== conversationId),
        // Clear active conversation if it was deleted
        ...(state.activeConversationId === conversationId ? {
          activeConversationId: null,
          messages: [],
        } : {}),
      }));
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      set({ error: 'Failed to delete conversation' });
    }
  },

  updateConversation: async (conversationId, updates) => {
    try {
      const response = await fetch(`http://localhost:8000/api/conversations/${conversationId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      const updatedConversation = await response.json();

      // Update in conversations list
      set((state) => ({
        conversations: state.conversations.map((c) =>
          c.id === conversationId ? updatedConversation : c
        ),
      }));
    } catch (error) {
      console.error('Failed to update conversation:', error);
      set({ error: 'Failed to update conversation' });
    }
  },

  bulkDeleteConversations: async (conversationIds) => {
    try {
      await fetch('http://localhost:8000/api/conversations/bulk-delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_ids: conversationIds }),
      });

      // Remove from conversations list
      set((state) => ({
        conversations: state.conversations.filter((c) => !conversationIds.includes(c.id)),
        // Clear active conversation if it was deleted
        ...(state.activeConversationId && conversationIds.includes(state.activeConversationId) ? {
          activeConversationId: null,
          messages: [],
        } : {}),
      }));
    } catch (error) {
      console.error('Failed to bulk delete conversations:', error);
      set({ error: 'Failed to bulk delete conversations' });
    }
  },

  deleteAllConversations: async () => {
    try {
      await fetch('http://localhost:8000/api/conversations/all', {
        method: 'DELETE',
      });

      // Clear all conversations
      set({
        conversations: [],
        activeConversationId: null,
        messages: [],
      });
    } catch (error) {
      console.error('Failed to delete all conversations:', error);
      set({ error: 'Failed to delete all conversations' });
    }
  },

  startNewConversation: () => {
    set({
      activeConversationId: null,
      messages: [],
      isStreaming: false,
      streamingContent: '',
      currentToolExecutions: [],
      currentSearchResults: [],
      currentWebSearchResults: [],
      currentKnowledgeGraph: [],
      currentTemporalData: [],
      error: null,
    });
  },

  // ============================================================================
  // Collection Management
  // ============================================================================

  loadCollections: async () => {
    try {
      const collections = await ragApi.listCollections();
      set({ collections });
    } catch (error) {
      console.error('Failed to load collections:', error);
    }
  },

  createCollection: async (name, description, domain, domainScope) => {
    try {
      await ragApi.createCollection(name, description, domain, domainScope);
      // Reload collections
      const collections = await ragApi.listCollections();
      set({ collections });
    } catch (error) {
      console.error('Failed to create collection:', error);
      throw error;
    }
  },

  selectCollection: (collectionId) => {
    set({ selectedCollectionId: collectionId });
  },

  loadDocuments: async (collectionName) => {
    try {
      const documents = await ragApi.listDocuments(collectionName);
      set({ documents });
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  },

  selectDocument: (documentId) => {
    set({ selectedDocumentId: documentId });
  },

  setInputValue: (value) => {
    set({ inputValue: value });
  },

  searchDocuments: async (query, collectionName) => {
    try {
      const searchResults = await ragApi.searchDocuments(query, collectionName);
      set({ searchResults });
    } catch (error) {
      console.error('Failed to search documents:', error);
    }
  },

  queryRelationships: async (query, collectionName) => {
    try {
      const knowledgeGraphData = await ragApi.queryRelationships(query, collectionName);
      set({ knowledgeGraphData });
    } catch (error) {
      console.error('Failed to query relationships:', error);
    }
  },

  // ============================================================================
  // Tool Approval Actions
  // ============================================================================

  approvePendingTools: async () => {
    const { pendingToolConversationId, sseClient } = get();

    if (!pendingToolConversationId) {
      console.error('No pending tool conversation ID');
      return;
    }

    // Clear pending state and start streaming again
    set({
      pendingToolCalls: [],
      pendingToolConversationId: null,
      isStreaming: true,
    });

    // Call approve endpoint via SSE client
    if (sseClient) {
      try {
        const response = await fetch('http://localhost:8000/api/chat/approve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ conversation_id: pendingToolConversationId }),
        });

        if (!response.ok) {
          throw new Error(`Approval failed: ${response.statusText}`);
        }

        // Handle SSE stream from approval
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (reader) {
          let buffer = '';
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const event = JSON.parse(line.slice(6));
                  // Reuse existing event handlers
                  const state = get();
                  if (event.type === 'token') {
                    set({ streamingContent: state.streamingContent + event.content });
                  } else if (event.type === 'done') {
                    const { streamingContent, messages } = get();
                    if (streamingContent) {
                      set({
                        messages: [...messages, {
                          id: Date.now(),
                          role: 'assistant',
                          content: streamingContent,
                          created_at: new Date().toISOString(),
                        }],
                        streamingContent: '',
                        isStreaming: false,
                        currentToolExecutions: [],
                      });
                    } else {
                      set({ isStreaming: false });
                    }
                  } else if (event.type === 'tool_start' && event.tool) {
                    set((state) => ({
                      currentToolExecutions: [...state.currentToolExecutions, {
                        id: event.tool.id,
                        name: event.tool.name,
                        status: 'running' as const,
                        startTime: Date.now(),
                      }],
                    }));
                  } else if (event.type === 'tool_end' && event.tool) {
                    set((state) => ({
                      currentToolExecutions: state.currentToolExecutions.map((exec) =>
                        exec.id === event.tool!.id
                          ? {
                              ...exec,
                              status: event.tool!.status === 'error' ? 'failed' : 'completed',
                              endTime: Date.now(),
                              error: event.tool!.error,
                            }
                          : exec
                      ),
                    }));
                    // Refresh collections if create_collection completed successfully
                    if (event.tool.name === 'create_collection' && event.tool.status !== 'error') {
                      get().loadCollections();
                    }
                  } else if (event.type === 'tool_proposal' && event.tools) {
                    // Another tool proposal - show approval UI again
                    const { streamingContent, messages } = get();
                    if (streamingContent) {
                      set({
                        messages: [...messages, {
                          id: Date.now(),
                          role: 'assistant',
                          content: streamingContent,
                          created_at: new Date().toISOString(),
                        }],
                        streamingContent: '',
                      });
                    }
                    set({
                      pendingToolCalls: event.tools,
                      pendingToolConversationId: event.conversation_id || pendingToolConversationId,
                      isStreaming: false,
                    });
                  } else if (event.type === 'open_modal' && event.modal === 'ingestion') {
                    // Agent requested to open the ingestion modal
                    const tab = event.tab || 'file';
                    const params = event.params || {};
                    set({
                      ingestionModalOpen: true,
                      ingestionModalTab: tab,
                      ingestionModalParams: params,
                    });
                  } else if (event.type === 'search_results' && event.results) {
                    set({ currentSearchResults: event.results as SearchResult[] });
                  } else if (event.type === 'error') {
                    set({ error: event.message || 'Approval error', isStreaming: false });
                  }
                } catch (e) {
                  console.error('Failed to parse SSE event:', e);
                }
              }
            }
          }
        }
      } catch (error) {
        console.error('Failed to approve tools:', error);
        set({ error: 'Failed to approve tools', isStreaming: false });
      }
    }
  },

  rejectPendingTools: async (reason) => {
    const { pendingToolConversationId } = get();

    if (!pendingToolConversationId) {
      console.error('No pending tool conversation ID');
      return;
    }

    // Clear pending state and start streaming again
    set({
      pendingToolCalls: [],
      pendingToolConversationId: null,
      isStreaming: true,
    });

    try {
      const response = await fetch('http://localhost:8000/api/chat/reject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: pendingToolConversationId,
          reason: reason,
        }),
      });

      if (!response.ok) {
        throw new Error(`Rejection failed: ${response.statusText}`);
      }

      // Handle SSE stream from rejection (similar to approval)
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event = JSON.parse(line.slice(6));
                if (event.type === 'token') {
                  set((state) => ({ streamingContent: state.streamingContent + event.content }));
                } else if (event.type === 'done') {
                  const { streamingContent, messages } = get();
                  if (streamingContent) {
                    set({
                      messages: [...messages, {
                        id: Date.now(),
                        role: 'assistant',
                        content: streamingContent,
                        created_at: new Date().toISOString(),
                      }],
                      streamingContent: '',
                      isStreaming: false,
                    });
                  } else {
                    set({ isStreaming: false });
                  }
                } else if (event.type === 'tool_proposal' && event.tools) {
                  // Agent proposed new tools after rejection
                  const { streamingContent, messages } = get();
                  if (streamingContent) {
                    set({
                      messages: [...messages, {
                        id: Date.now(),
                        role: 'assistant',
                        content: streamingContent,
                        created_at: new Date().toISOString(),
                      }],
                      streamingContent: '',
                    });
                  }
                  set({
                    pendingToolCalls: event.tools,
                    pendingToolConversationId: event.conversation_id || pendingToolConversationId,
                    isStreaming: false,
                  });
                } else if (event.type === 'error') {
                  set({ error: event.message || 'Rejection error', isStreaming: false });
                }
              } catch (e) {
                console.error('Failed to parse SSE event:', e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to reject tools:', error);
      set({ error: 'Failed to reject tools', isStreaming: false });
    }
  },

  revisePendingTools: async (revisedTools) => {
    const { pendingToolConversationId } = get();

    if (!pendingToolConversationId) {
      console.error('No pending tool conversation ID');
      return;
    }

    // Clear pending state and start streaming again
    set({
      pendingToolCalls: [],
      pendingToolConversationId: null,
      isStreaming: true,
    });

    try {
      const response = await fetch('http://localhost:8000/api/chat/revise', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: pendingToolConversationId,
          tools: revisedTools,
        }),
      });

      if (!response.ok) {
        throw new Error(`Revision failed: ${response.statusText}`);
      }

      // Handle SSE stream (same as approval)
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event = JSON.parse(line.slice(6));
                if (event.type === 'token') {
                  set((state) => ({ streamingContent: state.streamingContent + event.content }));
                } else if (event.type === 'done') {
                  const { streamingContent, messages } = get();
                  if (streamingContent) {
                    set({
                      messages: [...messages, {
                        id: Date.now(),
                        role: 'assistant',
                        content: streamingContent,
                        created_at: new Date().toISOString(),
                      }],
                      streamingContent: '',
                      isStreaming: false,
                      currentToolExecutions: [],
                    });
                  } else {
                    set({ isStreaming: false });
                  }
                } else if (event.type === 'tool_start' && event.tool) {
                  set((state) => ({
                    currentToolExecutions: [...state.currentToolExecutions, {
                      id: event.tool.id,
                      name: event.tool.name,
                      status: 'running' as const,
                      startTime: Date.now(),
                    }],
                  }));
                } else if (event.type === 'tool_end' && event.tool) {
                  set((state) => ({
                    currentToolExecutions: state.currentToolExecutions.map((exec) =>
                      exec.id === event.tool!.id
                        ? {
                            ...exec,
                            status: event.tool!.status === 'error' ? 'failed' : 'completed',
                            endTime: Date.now(),
                            error: event.tool!.error,
                          }
                        : exec
                    ),
                  }));
                  // Refresh collections if create_collection completed successfully
                  if (event.tool.name === 'create_collection' && event.tool.status !== 'error') {
                    get().loadCollections();
                  }
                } else if (event.type === 'tool_proposal' && event.tools) {
                  const { streamingContent, messages } = get();
                  if (streamingContent) {
                    set({
                      messages: [...messages, {
                        id: Date.now(),
                        role: 'assistant',
                        content: streamingContent,
                        created_at: new Date().toISOString(),
                      }],
                      streamingContent: '',
                    });
                  }
                  set({
                    pendingToolCalls: event.tools,
                    pendingToolConversationId: event.conversation_id || pendingToolConversationId,
                    isStreaming: false,
                  });
                } else if (event.type === 'open_modal' && event.modal === 'ingestion') {
                  // Agent requested to open the ingestion modal
                  const tab = event.tab || 'file';
                  const params = event.params || {};
                  set({
                    ingestionModalOpen: true,
                    ingestionModalTab: tab,
                    ingestionModalParams: params,
                  });
                } else if (event.type === 'search_results' && event.results) {
                  set({ currentSearchResults: event.results as SearchResult[] });
                } else if (event.type === 'error') {
                  set({ error: event.message || 'Revision error', isStreaming: false });
                }
              } catch (e) {
                console.error('Failed to parse SSE event:', e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to revise tools:', error);
      set({ error: 'Failed to revise tools', isStreaming: false });
    }
  },

  clearPendingTools: () => {
    set({
      pendingToolCalls: [],
      pendingToolConversationId: null,
    });
  },

  // ============================================================================
  // Agent-Triggered Modal Actions
  // ============================================================================

  openIngestionModal: (tab, params) => {
    set({
      ingestionModalOpen: true,
      ingestionModalTab: tab,
      ingestionModalParams: params,
    });
  },

  closeIngestionModal: () => {
    set({
      ingestionModalOpen: false,
      ingestionModalTab: 'file',
      ingestionModalParams: {},
    });
  },

  reset: () => {
    set({
      messages: [],
      conversations: [],
      isStreaming: false,
      streamingContent: '',
      activeConversationId: null,
      currentToolExecutions: [],
      error: null,
      searchResults: [],
      knowledgeGraphData: [],
      currentSearchResults: [],
      currentWebSearchResults: [],
      currentKnowledgeGraph: [],
      currentTemporalData: [],
      pendingToolCalls: [],
      pendingToolConversationId: null,
      ingestionModalOpen: false,
      ingestionModalTab: 'file',
      ingestionModalParams: {},
    });
  },
}));
