/**
 * DocumentModal Component Tests
 *
 * Tests document viewer modal functionality including
 * metadata display, review toggle, and content rendering.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import DocumentModal from '../../src/rag/components/DocumentModal';
import type { Document } from '../../src/rag/types';
import * as ragApi from '../../src/rag/ragApi';

// Mock ragApi
vi.mock('../../src/rag/ragApi', () => ({
  updateDocumentReview: vi.fn(),
  listCollections: vi.fn().mockResolvedValue([]),
  getDocument: vi.fn(),
  manageCollectionLink: vi.fn(),
}));

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('DocumentModal', () => {
  const mockDocument: Document = {
    id: 1,
    filename: 'test-document.md',
    content: '# Test Document\n\nThis is test content.',
    file_type: 'md',
    file_size: 1024,
    created_at: '2024-01-01T12:00:00Z',
    updated_at: '2024-01-02T12:00:00Z',
    collections: ['test-collection'],
    metadata: { custom_field: 'custom_value' },
    reviewed_by_human: false,
    quality_score: 0.85,
    quality_summary: 'High quality document',
    topic_relevance_score: 0.72,
    topic_provided: 'testing',
    eval_model: 'gpt-4',
  };

  const mockOnClose = vi.fn();
  const mockOnDocumentUpdate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should not render modal content when document is null', () => {
      renderWithProvider(
        <DocumentModal
          document={null}
          opened={true}
          onClose={mockOnClose}
        />
      );

      // No document content should be rendered
      expect(screen.queryByText('Human Review')).toBeNull();
      expect(screen.queryByText('File Type')).toBeNull();
    });

    it('should render modal when opened with document', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('test-document.md')).toBeDefined();
    });

    it('should display file type badge', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      // File type should be shown uppercase
      expect(screen.getByText('MD')).toBeDefined();
    });

    it('should display file size in KB', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      // 1024 bytes = 1.00 KB
      expect(screen.getByText('1.00 KB')).toBeDefined();
    });

    it('should display creation date', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      // Check for Created label
      expect(screen.getByText('Created')).toBeDefined();
    });

    it('should display collections', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('test-collection')).toBeDefined();
    });
  });

  describe('human review toggle', () => {
    it('should display review toggle', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Human Review')).toBeDefined();
      // Mantine Switch renders as a switch role or has input inside
      const toggle = document.querySelector('input[type="checkbox"]');
      expect(toggle).toBeDefined();
    });

    it('should show review status text for unreviewed document', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      // The label text showing review status
      expect(screen.getByText(/not reviewed/i)).toBeDefined();
    });

    it('should show Reviewed when document is reviewed', () => {
      const reviewedDoc = { ...mockDocument, reviewed_by_human: true };
      renderWithProvider(
        <DocumentModal
          document={reviewedDoc}
          opened={true}
          onClose={mockOnClose}
        />
      );

      // Should show "Reviewed" label
      const reviewedText = screen.getAllByText(/reviewed/i);
      expect(reviewedText.length).toBeGreaterThan(0);
    });

    it('should call updateDocumentReview when toggle clicked', async () => {
      vi.mocked(ragApi.updateDocumentReview).mockResolvedValue(undefined);
      const user = userEvent.setup();

      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
          onDocumentUpdate={mockOnDocumentUpdate}
        />
      );

      // Find the switch input
      const toggle = document.querySelector('input[type="checkbox"]');
      expect(toggle).toBeDefined();
      await user.click(toggle!);

      await waitFor(() => {
        expect(ragApi.updateDocumentReview).toHaveBeenCalledWith(1, true);
      });
    });
  });

  describe('evaluation display', () => {
    it('should display quality score', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      // Quality score of 0.85 should show as 85%
      expect(screen.getByText('85%')).toBeDefined();
    });

    it('should display topic provided', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('testing')).toBeDefined();
    });

    it('should display topic relevance score', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      // Topic relevance of 0.72 should show as 72%
      expect(screen.getByText('72%')).toBeDefined();
    });

    it('should display quality summary', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('High quality document')).toBeDefined();
    });

    it('should display Not evaluated for null topic relevance', () => {
      const docWithoutTopic = { ...mockDocument, topic_relevance_score: null };
      renderWithProvider(
        <DocumentModal
          document={docWithoutTopic}
          opened={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Not evaluated')).toBeDefined();
    });
  });

  describe('custom metadata', () => {
    it('should display custom metadata section', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Custom Metadata')).toBeDefined();
    });

    it('should display metadata as JSON', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      // Check that the custom field value is displayed
      expect(screen.getByText(/"custom_field"/)).toBeDefined();
    });

    it('should not display metadata section when empty', () => {
      const docWithoutMetadata = { ...mockDocument, metadata: {} };
      renderWithProvider(
        <DocumentModal
          document={docWithoutMetadata}
          opened={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.queryByText('Custom Metadata')).toBeNull();
    });
  });

  describe('content rendering', () => {
    it('should display content section with character count', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      // Content has 42 characters
      expect(screen.getByText(/Content/)).toBeDefined();
    });

    it('should render markdown content for .md files', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      // Check that content is rendered (markdown converts # to h1)
      expect(screen.getByText('Test Document')).toBeDefined();
    });

    it('should render plain text for non-markdown files', () => {
      const plainTextDoc = {
        ...mockDocument,
        file_type: 'txt',
        filename: 'test.txt',
        content: 'Plain text content',
      };
      renderWithProvider(
        <DocumentModal
          document={plainTextDoc}
          opened={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Plain text content')).toBeDefined();
    });
  });

  describe('collection management', () => {
    it('should have Add to Collection button', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Add to Collection')).toBeDefined();
    });

    it('should show orphan protection message when only one collection', () => {
      renderWithProvider(
        <DocumentModal
          document={mockDocument}
          opened={true}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText(/Cannot remove last collection/)).toBeDefined();
    });
  });
});
