/**
 * TypeScript interfaces for RAG Memory Web
 */

// ============================================================================
// Chat & Conversations
// ============================================================================

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string | null;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: number;
}

// ============================================================================
// Starter Prompts
// ============================================================================

export interface StarterPrompt {
  id: number;
  prompt_text: string;
  category: string | null;
  has_placeholder: boolean;
  display_order: number;
}

// ============================================================================
// Collections
// ============================================================================

export interface Collection {
  name: string;
  description: string;
  domain: string;
  domain_scope: string;
  created_at: string;
}

export interface CollectionInfo {
  name: string;
  description: string;
  document_count: number;
  chunk_count: number;
  created_at: string;
  sample_documents: string[]; // Array of document filenames/titles
  crawled_urls: Array<{
    url: string;
    timestamp: string;
    page_count: number;
    chunk_count: number;
  }>;
  domain?: string; // Optional - may not be returned by backend
  domain_scope?: string; // Optional - may not be returned by backend
}

// Metadata schema for a collection (custom fields defined at creation)
export interface CollectionMetadataSchema {
  collection_name: string;
  description: string;
  document_count: number;
  metadata_schema: {
    mandatory: Record<string, string>;
    custom: Record<string, {
      type: string;
      description?: string;
      required?: boolean;
      enum?: string[];
    }>;
    system: string[];
  };
  custom_fields: Record<string, {
    type: string;
    description?: string;
    required?: boolean;
    enum?: string[];
  }>;
  system_fields: string[];
}

// ============================================================================
// Documents
// ============================================================================

export interface Document {
  id: number;
  filename: string;
  content: string;
  file_type: string;
  file_size: number;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  collections: string[];
  // Evaluation fields
  reviewed_by_human?: boolean;
  quality_score?: number;           // 0.0-1.0
  quality_summary?: string;
  topic_relevance_score?: number;   // 0.0-1.0, null if no topic was used
  topic_relevance_summary?: string;
  topic_provided?: string;
  eval_model?: string;
  eval_timestamp?: string;
}

export interface DocumentListItem {
  id: number;
  filename: string;
  chunk_count: number;
}

// Extended document list item with evaluation fields (when include_details=true)
export interface DocumentListItemDetailed extends DocumentListItem {
  file_type: string;
  file_size: number;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
  collections: string[];
  // Evaluation fields
  reviewed_by_human: boolean;
  quality_score: number | null;        // 0.0-1.0, null for legacy docs
  topic_relevance_score: number | null; // 0.0-1.0, null if no topic was provided
  topic_provided: string | null;        // The topic used for evaluation, or null
}

// ============================================================================
// Evaluation (from LLM content assessment)
// ============================================================================

export interface EvaluationResult {
  quality_score: number;           // 0.0-1.0, always populated
  quality_summary: string;         // always populated
  topic_relevance_score?: number;  // 0.0-1.0, only when topic provided
  topic_relevance_summary?: string; // only when topic provided
  topic_provided?: string;             // echo of provided topic
}

export interface IngestResponse {
  source_document_id: number;
  num_chunks: number;
  entities_extracted?: number;
  filename?: string;
  file_type?: string;
  file_size?: number;
  collection_name: string;
  evaluation?: EvaluationResult;
}

// ============================================================================
// Search Results
// ============================================================================

export interface SearchResult {
  content: string;
  similarity: number;
  source_document_id: number;
  source_filename: string;
  chunk_id?: number;
  chunk_index?: number;
  char_start?: number;
  char_end?: number;
  metadata?: Record<string, any>;
  // Evaluation fields (from source document)
  reviewed_by_human?: boolean;
  quality_score?: number;           // 0.0-1.0
  topic_relevance_score?: number;   // 0.0-1.0, null if no topic was used during ingest
}

// ============================================================================
// Knowledge Graph
// ============================================================================

export interface RelationshipResult {
  id: string;
  relationship_type: string;
  fact: string;
  source_node_id: string;
  target_node_id: string;
  source_node_name?: string;  // Entity name for source node (fetched from knowledge graph)
  target_node_name?: string;  // Entity name for target node (fetched from knowledge graph)
  valid_from: string;
  valid_until: string;
}

export interface TemporalResult {
  fact: string;
  relationship_type: string;
  valid_from: string;
  valid_until: string;
  status: 'current' | 'superseded';
  created_at: string;
  expired_at: string | null;
}

// ============================================================================
// Web Search (from Python tools)
// ============================================================================

export interface WebSearchResult {
  title: string;
  url: string;
  snippet: string;
  source?: string;
}

// ============================================================================
// SSE Stream Events
// ============================================================================

export type SSEEventType =
  | 'token'
  | 'done'
  | 'error'
  | 'metadata'
  | 'tool_start'
  | 'tool_end'
  | 'tool_proposal'
  | 'search_results'
  | 'web_search_results'
  | 'knowledge_graph'
  | 'temporal_data'
  | 'open_modal';

// Tool proposal for user approval
export interface PendingToolCall {
  id: string;
  name: string;
  args: Record<string, any>;
}

export interface ToolExecution {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'failed';
  startTime: number;
  endTime?: number;
  error?: string;
}

// Modal parameters for agent-triggered dialogs
export interface IngestionModalParams {
  collection_name?: string;
  topic?: string;
  mode?: 'ingest' | 'reingest';
  reviewed_by_human?: boolean;
}

export interface SSEEvent {
  type: SSEEventType;
  content?: string;
  error?: string;
  metadata?: {
    conversation_id?: number;
    message_id?: number;
  };
  tool?: {
    id: string;
    name: string;
    status?: 'start' | 'end' | 'error';
    error?: string;
  };
  // Tool proposal for user approval
  tools?: PendingToolCall[];
  conversation_id?: number;
  // Structured data for rich UI components
  results?: SearchResult[] | WebSearchResult[];
  data?: RelationshipResult[];
  timeline?: TemporalResult[];
  // Modal control (from open_file_upload_dialog tool)
  modal?: string;
  tab?: 'file' | 'directory';
  params?: IngestionModalParams;
}

// ============================================================================
// UI State
// ============================================================================

export interface RagState {
  // Chat state
  messages: ChatMessage[];
  conversations: Conversation[];
  isConnected: boolean;
  isStreaming: boolean;
  streamingContent: string;
  sseClient: ChatSSEClient | null;
  activeConversationId: number | null;
  currentToolExecutions: ToolExecution[];
  error: string | null;
  inputValue: string;

  // RAG-specific state
  collections: Collection[];
  selectedCollectionId: string | null;
  documents: DocumentListItem[];
  selectedDocumentId: number | null;
  searchResults: SearchResult[];
  knowledgeGraphData: RelationshipResult[];

  // Rich content from streaming events (cleared after each message)
  currentSearchResults: SearchResult[];
  currentWebSearchResults: WebSearchResult[];
  currentKnowledgeGraph: RelationshipResult[];
  currentTemporalData: TemporalResult[];

  // Tool approval state
  pendingToolCalls: PendingToolCall[];
  pendingToolConversationId: number | null;

  // Agent-triggered modal state
  ingestionModalOpen: boolean;
  ingestionModalTab: 'file' | 'directory' | 'url' | 'text';
  ingestionModalParams: IngestionModalParams;

  // Actions
  connect: (getToken: () => Promise<string | null>) => void;
  disconnect: () => void;
  sendMessage: (content: string) => Promise<void>;

  // Conversation management
  loadConversations: () => Promise<void>;
  selectConversation: (conversationId: number) => Promise<void>;
  deleteConversation: (conversationId: number) => Promise<void>;
  updateConversation: (conversationId: number, updates: { title?: string; is_pinned?: boolean }) => Promise<void>;
  bulkDeleteConversations: (conversationIds: number[]) => Promise<void>;
  deleteAllConversations: () => Promise<void>;
  startNewConversation: () => void;

  // Collection management
  loadCollections: () => Promise<void>;
  createCollection: (name: string, description: string, domain: string, domainScope: string) => Promise<void>;
  selectCollection: (collectionId: string | null) => void;

  // Document management
  loadDocuments: (collectionName: string) => Promise<void>;
  selectDocument: (documentId: number | null) => void;

  // Search
  setInputValue: (value: string) => void;
  searchDocuments: (query: string, collectionName?: string) => Promise<void>;
  queryRelationships: (query: string, collectionName?: string) => Promise<void>;

  // Tool approval actions
  approvePendingTools: () => Promise<void>;
  rejectPendingTools: (reason?: string) => Promise<void>;
  revisePendingTools: (revisedTools: PendingToolCall[]) => Promise<void>;
  clearPendingTools: () => void;

  // Agent-triggered modal actions
  openIngestionModal: (tab: 'file' | 'directory' | 'url' | 'text', params: IngestionModalParams) => void;
  closeIngestionModal: () => void;

  reset: () => void;
}

// Placeholder for ChatSSEClient class (implemented in api.ts)
export interface ChatSSEClient {
  send: (message: string) => void;
  close: () => void;
}
