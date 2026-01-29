/**
 * MessageList Component Tests
 *
 * Tests message list rendering, streaming, and rich content display.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import MessageList from '../../src/rag/components/MessageList';
import { useRagStore } from '../../src/rag/store';

// Mock child components that have complex dependencies
vi.mock('../../src/rag/components/SearchResults', () => ({
  default: ({ results }: { results: unknown[] }) => (
    <div data-testid="search-results">Search Results: {results.length}</div>
  ),
}));

vi.mock('../../src/rag/components/WebSearchResults', () => ({
  default: ({ results }: { results: unknown[] }) => (
    <div data-testid="web-search-results">Web Results: {results.length}</div>
  ),
}));

vi.mock('../../src/rag/components/KnowledgeGraphView', () => ({
  default: ({ relationships }: { relationships: unknown[] }) => (
    <div data-testid="knowledge-graph">Graph: {relationships.length}</div>
  ),
}));

vi.mock('../../src/rag/components/TemporalTimeline', () => ({
  default: ({ timeline }: { timeline: unknown[] }) => (
    <div data-testid="temporal-timeline">Timeline: {timeline.length}</div>
  ),
}));

vi.mock('../../src/rag/components/ToolProposalCard', () => ({
  default: ({ tools }: { tools: unknown[] }) => (
    <div data-testid="tool-proposal">Tools: {tools.length}</div>
  ),
}));

vi.mock('../../src/rag/components/DocumentModal', () => ({
  default: ({ opened }: { opened: boolean }) =>
    opened ? <div data-testid="doc-modal">Document Modal</div> : null,
}));

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('MessageList', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Reset store state
    useRagStore.setState({
      messages: [],
      streamingContent: '',
      isStreaming: false,
      currentSearchResults: [],
      currentWebSearchResults: [],
      currentKnowledgeGraph: [],
      currentTemporalData: [],
      currentToolExecutions: [],
      pendingToolCalls: [],
      approvePendingTools: vi.fn(),
      rejectPendingTools: vi.fn(),
      revisePendingTools: vi.fn(),
      sendMessage: vi.fn(),
    });
  });

  describe('message rendering', () => {
    it('should render messages from store', () => {
      useRagStore.setState({
        messages: [
          { id: 1, role: 'user', content: 'Hello', created_at: '2024-01-01T12:00:00Z' },
          { id: 2, role: 'assistant', content: 'Hi there!', created_at: '2024-01-01T12:00:01Z' },
        ],
      });

      renderWithProvider(<MessageList />);

      expect(screen.getByText('Hello')).toBeDefined();
      expect(screen.getByText('Hi there!')).toBeDefined();
    });

    it('should render empty when no messages', () => {
      renderWithProvider(<MessageList />);

      // Should not crash, just render empty
      expect(screen.queryByText('You')).toBeNull();
      expect(screen.queryByText('Assistant')).toBeNull();
    });

    it('should render multiple messages in order', () => {
      useRagStore.setState({
        messages: [
          { id: 1, role: 'user', content: 'First', created_at: '2024-01-01T12:00:00Z' },
          { id: 2, role: 'assistant', content: 'Second', created_at: '2024-01-01T12:00:01Z' },
          { id: 3, role: 'user', content: 'Third', created_at: '2024-01-01T12:00:02Z' },
        ],
      });

      renderWithProvider(<MessageList />);

      expect(screen.getByText('First')).toBeDefined();
      expect(screen.getByText('Second')).toBeDefined();
      expect(screen.getByText('Third')).toBeDefined();
    });
  });

  describe('streaming', () => {
    it('should show streaming message when isStreaming is true', () => {
      useRagStore.setState({
        isStreaming: true,
        streamingContent: 'Thinking about that...',
      });

      renderWithProvider(<MessageList />);

      expect(screen.getByText('Thinking about that...')).toBeDefined();
    });

    it('should not show streaming message when isStreaming is false', () => {
      useRagStore.setState({
        isStreaming: false,
        streamingContent: 'Old content',
      });

      renderWithProvider(<MessageList />);

      // Old streaming content should not be displayed
      expect(screen.queryByText('Old content')).toBeNull();
    });
  });

  describe('tool proposals', () => {
    it('should show tool proposal card when pending tools exist', () => {
      useRagStore.setState({
        pendingToolCalls: [
          { id: 't1', name: 'search_documents', args: { query: 'test' } },
        ],
      });

      renderWithProvider(<MessageList />);

      expect(screen.getByTestId('tool-proposal')).toBeDefined();
      expect(screen.getByText('Tools: 1')).toBeDefined();
    });

    it('should not show tool proposal card when no pending tools', () => {
      useRagStore.setState({
        pendingToolCalls: [],
      });

      renderWithProvider(<MessageList />);

      expect(screen.queryByTestId('tool-proposal')).toBeNull();
    });
  });

  describe('rich content', () => {
    it('should show search results when available and not streaming', () => {
      useRagStore.setState({
        isStreaming: false,
        currentSearchResults: [
          { content: 'Test result', similarity: 0.9, source_filename: 'test.md', source_document_id: 1 },
        ],
      });

      renderWithProvider(<MessageList />);

      expect(screen.getByTestId('search-results')).toBeDefined();
      expect(screen.getByText('Search Results: 1')).toBeDefined();
    });

    it('should hide search results while streaming', () => {
      useRagStore.setState({
        isStreaming: true,
        currentSearchResults: [
          { content: 'Test result', similarity: 0.9, source_filename: 'test.md', source_document_id: 1 },
        ],
      });

      renderWithProvider(<MessageList />);

      // Results should be hidden while streaming
      expect(screen.queryByTestId('search-results')).toBeNull();
    });

    it('should show knowledge graph when available and not streaming', () => {
      useRagStore.setState({
        isStreaming: false,
        currentKnowledgeGraph: [
          { id: 'r1', relationship_type: 'DEPENDS_ON', fact: 'Test', source_node_id: 'n1', target_node_id: 'n2' },
        ],
      });

      renderWithProvider(<MessageList />);

      expect(screen.getByTestId('knowledge-graph')).toBeDefined();
      expect(screen.getByText('Graph: 1')).toBeDefined();
    });

    it('should show temporal timeline when available and not streaming', () => {
      useRagStore.setState({
        isStreaming: false,
        currentTemporalData: [
          { fact: 'Update', relationship_type: 'VERSION', valid_from: '2024-01-01', valid_until: null, status: 'current' },
        ],
      });

      renderWithProvider(<MessageList />);

      expect(screen.getByTestId('temporal-timeline')).toBeDefined();
      expect(screen.getByText('Timeline: 1')).toBeDefined();
    });

    it('should show web search results when available and not streaming', () => {
      useRagStore.setState({
        isStreaming: false,
        currentWebSearchResults: [
          { title: 'Web Result', url: 'https://example.com', snippet: 'Test' },
        ],
      });

      renderWithProvider(<MessageList />);

      expect(screen.getByTestId('web-search-results')).toBeDefined();
      expect(screen.getByText('Web Results: 1')).toBeDefined();
    });
  });
});
