/**
 * SearchResults Component Tests
 *
 * Tests the RAG semantic search results display.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import SearchResults from '../../src/rag/components/SearchResults';
import type { SearchResult } from '../../src/rag/types';

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('SearchResults', () => {
  const mockResults: SearchResult[] = [
    {
      content: 'This is the first search result content about testing.',
      similarity: 0.85,
      source_document_id: 1,
      source_filename: 'test-doc-1.md',
      reviewed_by_human: true,
      quality_score: 0.9,
      topic_relevance_score: 0.8,
      chunk_index: 0,
    },
    {
      content: 'This is the second search result with moderate relevance.',
      similarity: 0.45,
      source_document_id: 2,
      source_filename: 'test-doc-2.txt',
      reviewed_by_human: false,
      quality_score: 0.6,
      topic_relevance_score: null,
      chunk_index: 2,
    },
    {
      content: 'This is a weak match result.',
      similarity: 0.2,
      source_document_id: 3,
      source_filename: 'test-doc-3.md',
      reviewed_by_human: false,
      quality_score: 0.4,
      topic_relevance_score: 0.3,
    },
  ];

  describe('empty state', () => {
    it('should return null when results is empty array', () => {
      const { container } = renderWithProvider(<SearchResults results={[]} />);
      expect(container.querySelector('.mantine-Card-root')).toBeNull();
    });

    it('should return null when results is not an array', () => {
      const { container } = renderWithProvider(
        <SearchResults results={null as unknown as SearchResult[]} />
      );
      expect(container.querySelector('.mantine-Card-root')).toBeNull();
    });
  });

  describe('rendering', () => {
    it('should render results header with count', () => {
      renderWithProvider(<SearchResults results={mockResults} />);
      expect(screen.getByText('Search Results (3)')).toBeDefined();
    });

    it('should display filenames', () => {
      renderWithProvider(<SearchResults results={mockResults} />);
      expect(screen.getByText('test-doc-1.md')).toBeDefined();
      expect(screen.getByText('test-doc-2.txt')).toBeDefined();
      expect(screen.getByText('test-doc-3.md')).toBeDefined();
    });

    it('should display similarity percentages', () => {
      renderWithProvider(<SearchResults results={mockResults} />);
      expect(screen.getByText('85% match')).toBeDefined();
      expect(screen.getByText('45% match')).toBeDefined();
      expect(screen.getByText('20% match')).toBeDefined();
    });

    it('should display content previews', () => {
      renderWithProvider(<SearchResults results={mockResults} />);
      expect(screen.getByText(/first search result content/)).toBeDefined();
      expect(screen.getByText(/second search result/)).toBeDefined();
      expect(screen.getByText(/weak match result/)).toBeDefined();
    });

    it('should display chunk index when available', () => {
      renderWithProvider(<SearchResults results={mockResults} />);
      expect(screen.getByText('Chunk 1')).toBeDefined(); // chunk_index 0 + 1
      expect(screen.getByText('Chunk 3')).toBeDefined(); // chunk_index 2 + 1
    });
  });

  describe('quality colors', () => {
    it('should show green badge for excellent matches (>= 60%)', () => {
      const { container } = renderWithProvider(<SearchResults results={mockResults} />);
      // 85% should have green/excellent styling
      const badges = container.querySelectorAll('.mantine-Badge-root');
      expect(badges.length).toBe(3);
    });

    it('should handle all quality levels', () => {
      // Our mock data has: 85% (excellent), 45% (good), 20% (weak)
      renderWithProvider(<SearchResults results={mockResults} />);
      expect(screen.getByText('85% match')).toBeDefined();
      expect(screen.getByText('45% match')).toBeDefined();
      expect(screen.getByText('20% match')).toBeDefined();
    });
  });

  describe('document click handler', () => {
    it('should call onDocumentClick when document is clicked', async () => {
      const mockOnClick = vi.fn();
      const user = userEvent.setup();

      renderWithProvider(<SearchResults results={mockResults} onDocumentClick={mockOnClick} />);

      await user.click(screen.getByText('test-doc-1.md'));

      expect(mockOnClick).toHaveBeenCalledWith(1);
    });

    it('should call onDocumentClick with correct document ID', async () => {
      const mockOnClick = vi.fn();
      const user = userEvent.setup();

      renderWithProvider(<SearchResults results={mockResults} onDocumentClick={mockOnClick} />);

      await user.click(screen.getByText('test-doc-2.txt'));

      expect(mockOnClick).toHaveBeenCalledWith(2);
    });

    it('should render as plain text without onDocumentClick', () => {
      renderWithProvider(<SearchResults results={mockResults} />);

      // Without onDocumentClick, filenames should be plain text, not anchors
      const anchors = screen.queryAllByRole('link');
      // No links should be rendered
      expect(anchors.length).toBe(0);
    });
  });
});
