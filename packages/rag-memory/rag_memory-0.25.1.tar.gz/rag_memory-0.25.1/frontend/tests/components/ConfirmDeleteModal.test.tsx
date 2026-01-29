/**
 * ConfirmDeleteModal Component Tests
 *
 * Tests the delete confirmation modal for collections and documents.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import { ConfirmDeleteModal, DeleteTarget } from '../../src/rag/components/modals/ConfirmDeleteModal';

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('ConfirmDeleteModal', () => {
  const mockOnClose = vi.fn();
  const mockOnConfirm = vi.fn().mockResolvedValue(undefined);

  const collectionTarget: DeleteTarget = {
    type: 'collection',
    name: 'test-collection',
    documentCount: 5,
  };

  const documentTarget: DeleteTarget = {
    type: 'document',
    name: 'test-document.md',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should return null when target is null', () => {
      const { container } = renderWithProvider(
        <ConfirmDeleteModal
          opened={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          target={null}
        />
      );

      // Should not render modal content
      expect(screen.queryByText('Delete Collection')).toBeNull();
      expect(screen.queryByText('Delete Document')).toBeNull();
    });

    it('should show Delete Collection title for collection targets', () => {
      renderWithProvider(
        <ConfirmDeleteModal
          opened={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          target={collectionTarget}
        />
      );

      // Use getAllByText since "Delete Collection" appears in both title and button
      const deleteTexts = screen.getAllByText('Delete Collection');
      expect(deleteTexts.length).toBeGreaterThanOrEqual(1);
    });

    it('should show Delete Document title for document targets', () => {
      renderWithProvider(
        <ConfirmDeleteModal
          opened={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          target={documentTarget}
        />
      );

      // Use getAllByText since "Delete Document" appears in both title and button
      const deleteTexts = screen.getAllByText('Delete Document');
      expect(deleteTexts.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('warning content', () => {
    it('should show warning about permanent action', () => {
      renderWithProvider(
        <ConfirmDeleteModal
          opened={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          target={collectionTarget}
        />
      );

      expect(screen.getByText(/This action cannot be undone/)).toBeDefined();
    });

    it('should display the target name', () => {
      renderWithProvider(
        <ConfirmDeleteModal
          opened={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          target={collectionTarget}
        />
      );

      expect(screen.getByText('"test-collection"')).toBeDefined();
    });

    it('should show document count for collection deletion', () => {
      renderWithProvider(
        <ConfirmDeleteModal
          opened={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          target={collectionTarget}
        />
      );

      expect(screen.getByText(/5/)).toBeDefined();
      expect(screen.getByText(/documents in this collection/)).toBeDefined();
    });
  });

  describe('buttons', () => {
    it('should have Cancel and Delete buttons', () => {
      renderWithProvider(
        <ConfirmDeleteModal
          opened={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          target={collectionTarget}
        />
      );

      expect(screen.getByRole('button', { name: 'Cancel' })).toBeDefined();
      expect(screen.getByRole('button', { name: 'Delete Collection' })).toBeDefined();
    });

    it('should call onClose when Cancel clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <ConfirmDeleteModal
          opened={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          target={collectionTarget}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Cancel' }));
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should call onConfirm when Delete clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <ConfirmDeleteModal
          opened={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          target={collectionTarget}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Delete Collection' }));

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalled();
      });
    });
  });

  describe('loading state', () => {
    it('should disable buttons when isDeleting is true', () => {
      renderWithProvider(
        <ConfirmDeleteModal
          opened={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          target={collectionTarget}
          isDeleting={true}
        />
      );

      expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled();
    });

    it('should show loading message when deleting', () => {
      renderWithProvider(
        <ConfirmDeleteModal
          opened={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          target={collectionTarget}
          isDeleting={true}
        />
      );

      expect(screen.getByText(/Deleting... Please wait/)).toBeDefined();
    });
  });
});
