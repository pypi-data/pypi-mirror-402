/**
 * DocumentsView Component Tests
 *
 * Tests document grid view with filtering and sorting.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import { DocumentsView } from '../../../src/rag/components/views/DocumentsView';
import { useRagStore } from '../../../src/rag/store';
import * as ragApi from '../../../src/rag/ragApi';
import type { DocumentListItemDetailed } from '../../../src/rag/types';

// Mock ragApi
vi.mock('../../../src/rag/ragApi', () => ({
  listDocuments: vi.fn(),
  getDocument: vi.fn(),
  deleteDocument: vi.fn(),
  listCollections: vi.fn().mockResolvedValue([]),
  updateDocumentReview: vi.fn(),
  manageCollectionLink: vi.fn(),
}));

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('DocumentsView', () => {
  const mockDocuments: DocumentListItemDetailed[] = [
    {
      id: 1,
      filename: 'document-one.md',
      chunk_count: 5,
      created_at: '2024-01-15T12:00:00Z',
      reviewed_by_human: true,
      quality_score: 0.85,
      topic_relevance_score: 0.72,
      topic_provided: 'testing',
    },
    {
      id: 2,
      filename: 'document-two.txt',
      chunk_count: 3,
      created_at: '2024-01-10T12:00:00Z',
      reviewed_by_human: false,
      quality_score: 0.55,
      topic_relevance_score: null,
      topic_provided: null,
    },
    {
      id: 3,
      filename: 'low-quality-doc.md',
      chunk_count: 2,
      created_at: '2024-01-05T12:00:00Z',
      reviewed_by_human: false,
      quality_score: 0.25,
      topic_relevance_score: 0.3,
      topic_provided: 'other',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    useRagStore.setState({
      collections: [
        { name: 'test-collection', description: 'Test', document_count: 3 },
      ],
    });
    vi.mocked(ragApi.listDocuments).mockResolvedValue(mockDocuments);
  });

  describe('rendering', () => {
    it('should show loading state initially', () => {
      vi.mocked(ragApi.listDocuments).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderWithProvider(<DocumentsView />);

      const loader = document.querySelector('.mantine-Loader-root');
      expect(loader).toBeDefined();
    });

    it('should display Documents title', async () => {
      renderWithProvider(<DocumentsView />);

      await waitFor(() => {
        expect(screen.getByText('Documents')).toBeDefined();
      });
    });

    it('should display Add Documents button', async () => {
      renderWithProvider(<DocumentsView />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add documents/i })).toBeDefined();
      });
    });

    it('should render document cards after loading', async () => {
      renderWithProvider(<DocumentsView />);

      await waitFor(() => {
        expect(screen.getByText('document-one.md')).toBeDefined();
        expect(screen.getByText('document-two.txt')).toBeDefined();
        expect(screen.getByText('low-quality-doc.md')).toBeDefined();
      });
    });

    it('should display document count', async () => {
      renderWithProvider(<DocumentsView />);

      await waitFor(() => {
        expect(screen.getByText(/showing 3 of 3 documents/i)).toBeDefined();
      });
    });

    it('should display chunk count badges', async () => {
      renderWithProvider(<DocumentsView />);

      await waitFor(() => {
        expect(screen.getByText('5 chunks')).toBeDefined();
        expect(screen.getByText('3 chunks')).toBeDefined();
      });
    });

    it('should display Reviewed badge for reviewed documents', async () => {
      renderWithProvider(<DocumentsView />);

      await waitFor(() => {
        expect(screen.getByText('Reviewed')).toBeDefined();
      });
    });

    it('should display quality score badges', async () => {
      renderWithProvider(<DocumentsView />);

      await waitFor(() => {
        expect(screen.getByText('Q: 85%')).toBeDefined();
        expect(screen.getByText('Q: 55%')).toBeDefined();
        expect(screen.getByText('Q: 25%')).toBeDefined();
      });
    });
  });

  describe('empty states', () => {
    it('should show empty state when no documents', async () => {
      vi.mocked(ragApi.listDocuments).mockResolvedValue([]);

      renderWithProvider(<DocumentsView />);

      await waitFor(() => {
        expect(screen.getByText('No documents yet')).toBeDefined();
      });
    });

    it('should show filter empty state when no matches', async () => {
      renderWithProvider(<DocumentsView />);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('document-one.md')).toBeDefined();
      });

      // Search for something that doesn't exist
      const searchInput = screen.getByPlaceholderText('Search by title...');
      await user.type(searchInput, 'nonexistent');

      await waitFor(() => {
        expect(screen.getByText('No matching documents')).toBeDefined();
      });
    });
  });

  describe('search filter', () => {
    it('should filter documents by search query', async () => {
      renderWithProvider(<DocumentsView />);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('document-one.md')).toBeDefined();
      });

      const searchInput = screen.getByPlaceholderText('Search by title...');
      await user.type(searchInput, 'one');

      await waitFor(() => {
        expect(screen.getByText('document-one.md')).toBeDefined();
        expect(screen.queryByText('document-two.txt')).toBeNull();
      });
    });
  });

  describe('review filter', () => {
    it('should filter by reviewed status', async () => {
      renderWithProvider(<DocumentsView />);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('document-one.md')).toBeDefined();
      });

      // Click on "✓ Reviewed" filter
      const reviewedButton = screen.getByRole('radio', { name: '✓ Reviewed' });
      await user.click(reviewedButton);

      await waitFor(() => {
        // Only reviewed document should be visible
        expect(screen.getByText('document-one.md')).toBeDefined();
        expect(screen.queryByText('document-two.txt')).toBeNull();
        expect(screen.queryByText('low-quality-doc.md')).toBeNull();
      });
    });

    it('should filter by not reviewed status', async () => {
      renderWithProvider(<DocumentsView />);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('document-one.md')).toBeDefined();
      });

      // Click on "Not Reviewed" filter
      const notReviewedButton = screen.getByRole('radio', { name: 'Not Reviewed' });
      await user.click(notReviewedButton);

      await waitFor(() => {
        expect(screen.queryByText('document-one.md')).toBeNull();
        expect(screen.getByText('document-two.txt')).toBeDefined();
        expect(screen.getByText('low-quality-doc.md')).toBeDefined();
      });
    });
  });

  describe('quality filter', () => {
    it('should filter by high quality', async () => {
      renderWithProvider(<DocumentsView />);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('document-one.md')).toBeDefined();
      });

      // Find quality filter group and click "High"
      const qualityHighButton = screen.getAllByRole('radio', { name: 'High' })[0];
      await user.click(qualityHighButton);

      await waitFor(() => {
        expect(screen.getByText('document-one.md')).toBeDefined();
        expect(screen.queryByText('document-two.txt')).toBeNull();
        expect(screen.queryByText('low-quality-doc.md')).toBeNull();
      });
    });

    it('should filter by low quality', async () => {
      renderWithProvider(<DocumentsView />);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('document-one.md')).toBeDefined();
      });

      // Find quality filter and click "Low"
      const qualityLowButton = screen.getAllByRole('radio', { name: 'Low' })[0];
      await user.click(qualityLowButton);

      await waitFor(() => {
        expect(screen.queryByText('document-one.md')).toBeNull();
        expect(screen.queryByText('document-two.txt')).toBeNull();
        expect(screen.getByText('low-quality-doc.md')).toBeDefined();
      });
    });
  });

  describe('topic filter', () => {
    it('should filter by no topic', async () => {
      renderWithProvider(<DocumentsView />);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('document-one.md')).toBeDefined();
      });

      // Find topic filter and click "None"
      const noneButton = screen.getByRole('radio', { name: 'None' });
      await user.click(noneButton);

      await waitFor(() => {
        expect(screen.queryByText('document-one.md')).toBeNull();
        expect(screen.getByText('document-two.txt')).toBeDefined();
        expect(screen.queryByText('low-quality-doc.md')).toBeNull();
      });
    });
  });

  describe('document interactions', () => {
    it('should open ingestion modal when Add Documents clicked', async () => {
      renderWithProvider(<DocumentsView />);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add documents/i })).toBeDefined();
      });

      await user.click(screen.getByRole('button', { name: /add documents/i }));

      await waitFor(() => {
        // Ingestion modal should open - check for modal content
        expect(screen.getByText('Ingest Content')).toBeDefined();
      });
    });

    it('should load document details when card clicked', async () => {
      const mockDocument = {
        id: 1,
        filename: 'document-one.md',
        content: 'Test content',
        file_type: 'md',
        file_size: 1024,
        created_at: '2024-01-15T12:00:00Z',
        updated_at: '2024-01-15T12:00:00Z',
        collections: ['test-collection'],
        metadata: {},
        reviewed_by_human: true,
        quality_score: 0.85,
      };
      vi.mocked(ragApi.getDocument).mockResolvedValue(mockDocument);

      renderWithProvider(<DocumentsView />);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('document-one.md')).toBeDefined();
      });

      // Click the document card
      await user.click(screen.getByText('document-one.md'));

      await waitFor(() => {
        expect(ragApi.getDocument).toHaveBeenCalledWith(1);
      });
    });
  });

  describe('API integration', () => {
    it('should call listDocuments on mount', async () => {
      renderWithProvider(<DocumentsView />);

      await waitFor(() => {
        expect(ragApi.listDocuments).toHaveBeenCalledWith(undefined, 1000, 0, true);
      });
    });

    it('should handle API errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(ragApi.listDocuments).mockRejectedValue(new Error('API error'));

      renderWithProvider(<DocumentsView />);

      await waitFor(() => {
        expect(screen.getByText('No documents yet')).toBeDefined();
      });

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });
});
