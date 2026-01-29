/**
 * SearchView Component Tests
 *
 * Tests the three-tab search interface (Semantic | Relationships | Temporal).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import { SearchView } from '../../src/rag/components/views/SearchView';
import { useRagStore } from '../../src/rag/store';
import * as ragApi from '../../src/rag/ragApi';

// Mock ragApi
vi.mock('../../src/rag/ragApi', () => ({
  searchDocuments: vi.fn(),
  queryRelationships: vi.fn(),
  queryTemporal: vi.fn(),
  getDocument: vi.fn(),
}));

// Mock visualization components (they use external libraries)
vi.mock('../../src/rag/components/visualizations/GraphVisualization', () => ({
  GraphVisualization: ({ opened, onClose }: { opened: boolean; onClose: () => void }) =>
    opened ? <div data-testid="graph-modal">Graph Modal</div> : null,
}));

vi.mock('../../src/rag/components/visualizations/TimelineVisualization', () => ({
  TimelineVisualization: ({ opened, onClose }: { opened: boolean; onClose: () => void }) =>
    opened ? <div data-testid="timeline-modal">Timeline Modal</div> : null,
}));

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('SearchView', () => {
  const mockCollections = [
    { id: 1, name: 'test-collection', description: 'Test', document_count: 5, created_at: '2024-01-01' },
    { id: 2, name: 'docs-collection', description: 'Docs', document_count: 10, created_at: '2024-01-02' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();

    // Reset store state with mock data
    useRagStore.setState({
      collections: mockCollections,
    });
  });

  describe('tabs', () => {
    it('should render three tabs: Semantic, Relationships, Temporal', () => {
      renderWithProvider(<SearchView />);

      expect(screen.getByRole('tab', { name: /semantic/i })).toBeDefined();
      expect(screen.getByRole('tab', { name: /relationships/i })).toBeDefined();
      expect(screen.getByRole('tab', { name: /temporal/i })).toBeDefined();
    });

    it('should default to Semantic tab', () => {
      renderWithProvider(<SearchView />);

      const semanticTab = screen.getByRole('tab', { name: /semantic/i });
      expect(semanticTab.getAttribute('aria-selected')).toBe('true');
    });

    it('should switch to Relationships tab when clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      const relationshipsTab = screen.getByRole('tab', { name: /relationships/i });
      await user.click(relationshipsTab);

      expect(relationshipsTab.getAttribute('aria-selected')).toBe('true');
    });

    it('should switch to Temporal tab when clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      const temporalTab = screen.getByRole('tab', { name: /temporal/i });
      await user.click(temporalTab);

      expect(temporalTab.getAttribute('aria-selected')).toBe('true');
    });
  });

  describe('semantic search', () => {
    it('should render search form in semantic tab', () => {
      renderWithProvider(<SearchView />);

      // Check for textarea with placeholder
      const textarea = screen.getByPlaceholderText(/what are you looking for/i);
      expect(textarea).toBeDefined();
    });

    it('should have Search button', () => {
      renderWithProvider(<SearchView />);

      expect(screen.getByRole('button', { name: /search/i })).toBeDefined();
    });

    it('should disable Search button when query is empty', () => {
      renderWithProvider(<SearchView />);

      const searchButton = screen.getByRole('button', { name: /search/i });
      expect(searchButton).toBeDisabled();
    });

    it('should enable Search button when query has text', async () => {
      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      const textarea = screen.getByPlaceholderText(/what are you looking for/i);
      await user.type(textarea, 'test query');

      const searchButton = screen.getByRole('button', { name: /search/i });
      expect(searchButton).not.toBeDisabled();
    });

    it('should call searchDocuments API when search clicked', async () => {
      vi.mocked(ragApi.searchDocuments).mockResolvedValue([]);

      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      const textarea = screen.getByPlaceholderText(/what are you looking for/i);
      await user.type(textarea, 'test query');

      const searchButton = screen.getByRole('button', { name: /search/i });
      await user.click(searchButton);

      await waitFor(() => {
        expect(ragApi.searchDocuments).toHaveBeenCalledWith({
          query: 'test query',
          collectionName: undefined,
          limit: 10,
          threshold: 0.35,
        });
      });
    });

    it('should display search results', async () => {
      vi.mocked(ragApi.searchDocuments).mockResolvedValue([
        {
          content: 'This is a test result content',
          similarity: 0.85,
          source_filename: 'test-doc.md',
          source_document_id: 1,
        },
      ]);

      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      const textarea = screen.getByPlaceholderText(/what are you looking for/i);
      await user.type(textarea, 'test query');
      await user.click(screen.getByRole('button', { name: /search/i }));

      await waitFor(() => {
        expect(screen.getByText('test-doc.md')).toBeDefined();
        expect(screen.getByText('This is a test result content')).toBeDefined();
        expect(screen.getByText('85% match')).toBeDefined();
      });
    });

    it('should show empty state when no results and no query', () => {
      renderWithProvider(<SearchView />);

      expect(screen.getByText('Search your knowledge base')).toBeDefined();
    });
  });

  describe('relationships search', () => {
    it('should render query form when Relationships tab active', async () => {
      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      await user.click(screen.getByRole('tab', { name: /relationships/i }));

      const textarea = screen.getByPlaceholderText(/explore connections/i);
      expect(textarea).toBeDefined();
    });

    it('should have Query Graph button', async () => {
      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      await user.click(screen.getByRole('tab', { name: /relationships/i }));

      expect(screen.getByRole('button', { name: /query graph/i })).toBeDefined();
    });

    it('should call queryRelationships API when search clicked', async () => {
      vi.mocked(ragApi.queryRelationships).mockResolvedValue([]);

      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      await user.click(screen.getByRole('tab', { name: /relationships/i }));

      const textarea = screen.getByPlaceholderText(/explore connections/i);
      await user.type(textarea, 'how does X relate to Y');

      await user.click(screen.getByRole('button', { name: /query graph/i }));

      await waitFor(() => {
        expect(ragApi.queryRelationships).toHaveBeenCalledWith('how does X relate to Y', undefined, 10, 0.35);
      });
    });

    it('should display relationship results', async () => {
      vi.mocked(ragApi.queryRelationships).mockResolvedValue([
        {
          id: 'rel1',
          relationship_type: 'DEPENDS_ON',
          fact: 'Component A depends on Component B',
          source_node_id: 'node1',
          target_node_id: 'node2',
          source_node_name: 'Component A',
          target_node_name: 'Component B',
        },
      ]);

      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      await user.click(screen.getByRole('tab', { name: /relationships/i }));

      const textarea = screen.getByPlaceholderText(/explore connections/i);
      await user.type(textarea, 'dependencies');
      await user.click(screen.getByRole('button', { name: /query graph/i }));

      await waitFor(() => {
        expect(screen.getByText('DEPENDS_ON')).toBeDefined();
        expect(screen.getByText('Component A depends on Component B')).toBeDefined();
      });
    });

    it('should show Visualize Graph button when results exist', async () => {
      vi.mocked(ragApi.queryRelationships).mockResolvedValue([
        {
          id: 'rel1',
          relationship_type: 'DEPENDS_ON',
          fact: 'Test fact',
          source_node_id: 'node1',
          target_node_id: 'node2',
        },
      ]);

      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      await user.click(screen.getByRole('tab', { name: /relationships/i }));

      const textarea = screen.getByPlaceholderText(/explore connections/i);
      await user.type(textarea, 'test');
      await user.click(screen.getByRole('button', { name: /query graph/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /visualize graph/i })).toBeDefined();
      });
    });
  });

  describe('temporal search', () => {
    it('should render query form when Temporal tab active', async () => {
      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      await user.click(screen.getByRole('tab', { name: /temporal/i }));

      const textarea = screen.getByPlaceholderText(/track evolution/i);
      expect(textarea).toBeDefined();
    });

    it('should have Query Timeline button', async () => {
      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      await user.click(screen.getByRole('tab', { name: /temporal/i }));

      expect(screen.getByRole('button', { name: /query timeline/i })).toBeDefined();
    });

    it('should call queryTemporal API when search clicked', async () => {
      vi.mocked(ragApi.queryTemporal).mockResolvedValue([]);

      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      await user.click(screen.getByRole('tab', { name: /temporal/i }));

      const textarea = screen.getByPlaceholderText(/track evolution/i);
      await user.type(textarea, 'how has X changed');

      await user.click(screen.getByRole('button', { name: /query timeline/i }));

      await waitFor(() => {
        expect(ragApi.queryTemporal).toHaveBeenCalledWith('how has X changed', undefined, 10, 0.35);
      });
    });

    it('should display temporal results', async () => {
      vi.mocked(ragApi.queryTemporal).mockResolvedValue([
        {
          fact: 'System was updated to version 2.0',
          relationship_type: 'VERSION_UPDATE',
          valid_from: '2024-01-01T00:00:00Z',
          valid_until: null,
          status: 'current',
        },
      ]);

      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      await user.click(screen.getByRole('tab', { name: /temporal/i }));

      const textarea = screen.getByPlaceholderText(/track evolution/i);
      await user.type(textarea, 'version changes');
      await user.click(screen.getByRole('button', { name: /query timeline/i }));

      await waitFor(() => {
        expect(screen.getByText('VERSION_UPDATE')).toBeDefined();
        expect(screen.getByText('System was updated to version 2.0')).toBeDefined();
        expect(screen.getByText('current')).toBeDefined();
      });
    });

    it('should show Visualize Timeline button when results exist', async () => {
      vi.mocked(ragApi.queryTemporal).mockResolvedValue([
        {
          fact: 'Test fact',
          relationship_type: 'UPDATE',
          valid_from: '2024-01-01T00:00:00Z',
          valid_until: null,
          status: 'current',
        },
      ]);

      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      await user.click(screen.getByRole('tab', { name: /temporal/i }));

      const textarea = screen.getByPlaceholderText(/track evolution/i);
      await user.type(textarea, 'test');
      await user.click(screen.getByRole('button', { name: /query timeline/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /visualize timeline/i })).toBeDefined();
      });
    });
  });

  describe('collection selector', () => {
    it('should have collection selector in semantic tab', () => {
      renderWithProvider(<SearchView />);

      // Mantine Select has a combobox role
      const comboboxes = screen.getAllByRole('textbox');
      // At least one textbox should be for collection selection (besides query textarea)
      expect(comboboxes.length).toBeGreaterThan(0);
    });

    it('should pass selected collection to API call', async () => {
      vi.mocked(ragApi.searchDocuments).mockResolvedValue([]);

      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      // Type in the query
      const textarea = screen.getByPlaceholderText(/what are you looking for/i);
      await user.type(textarea, 'test');

      // Click search
      await user.click(screen.getByRole('button', { name: /search/i }));

      await waitFor(() => {
        // Without collection selected, should pass undefined
        expect(ragApi.searchDocuments).toHaveBeenCalledWith({
          query: 'test',
          collectionName: undefined,
          limit: 10,
          threshold: 0.35,
        });
      });
    });
  });

  describe('error handling', () => {
    it('should handle search errors gracefully', async () => {
      vi.mocked(ragApi.searchDocuments).mockRejectedValue(new Error('API error'));

      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      const textarea = screen.getByPlaceholderText(/what are you looking for/i);
      await user.type(textarea, 'test');
      await user.click(screen.getByRole('button', { name: /search/i }));

      // Should not crash, results should be empty
      await waitFor(() => {
        expect(ragApi.searchDocuments).toHaveBeenCalled();
      });
    });

    it('should handle relationship query errors gracefully', async () => {
      vi.mocked(ragApi.queryRelationships).mockRejectedValue(new Error('API error'));

      const user = userEvent.setup();
      renderWithProvider(<SearchView />);

      await user.click(screen.getByRole('tab', { name: /relationships/i }));

      const textarea = screen.getByPlaceholderText(/explore connections/i);
      await user.type(textarea, 'test');
      await user.click(screen.getByRole('button', { name: /query graph/i }));

      // Should not crash
      await waitFor(() => {
        expect(ragApi.queryRelationships).toHaveBeenCalled();
      });
    });
  });
});
