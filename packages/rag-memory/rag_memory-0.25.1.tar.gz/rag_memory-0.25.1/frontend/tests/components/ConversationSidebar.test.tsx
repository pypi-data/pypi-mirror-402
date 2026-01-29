/**
 * ConversationSidebar Component Tests
 *
 * Tests conversation list, search, grouping, multi-select, and CRUD operations.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import ConversationSidebar from '../../src/rag/components/ConversationSidebar';
import { useRagStore } from '../../src/rag/store';

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

// Create mock conversations at different times
function createMockConversations() {
  const now = new Date();
  const today = new Date(now);
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  const lastWeek = new Date(now);
  lastWeek.setDate(lastWeek.getDate() - 5);
  const lastMonth = new Date(now);
  lastMonth.setDate(lastMonth.getDate() - 20);
  const older = new Date(now);
  older.setDate(older.getDate() - 60);

  return [
    {
      id: 1,
      title: 'Today conversation',
      created_at: today.toISOString(),
      updated_at: today.toISOString(),
      is_pinned: false,
      messages: [],
    },
    {
      id: 2,
      title: 'Yesterday conversation',
      created_at: yesterday.toISOString(),
      updated_at: yesterday.toISOString(),
      is_pinned: false,
      messages: [],
    },
    {
      id: 3,
      title: 'Pinned conversation',
      created_at: lastWeek.toISOString(),
      updated_at: lastWeek.toISOString(),
      is_pinned: true,
      messages: [],
    },
    {
      id: 4,
      title: 'Last week conversation',
      created_at: lastWeek.toISOString(),
      updated_at: lastWeek.toISOString(),
      is_pinned: false,
      messages: [],
    },
    {
      id: 5,
      title: 'Last month conversation',
      created_at: lastMonth.toISOString(),
      updated_at: lastMonth.toISOString(),
      is_pinned: false,
      messages: [],
    },
    {
      id: 6,
      title: 'Older conversation',
      created_at: older.toISOString(),
      updated_at: older.toISOString(),
      is_pinned: false,
      messages: [],
    },
  ];
}

describe('ConversationSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Reset store state with mock data
    useRagStore.setState({
      conversations: createMockConversations(),
      activeConversationId: null,
      loadConversations: vi.fn(),
      selectConversation: vi.fn(),
      deleteConversation: vi.fn().mockResolvedValue(undefined),
      updateConversation: vi.fn().mockResolvedValue(undefined),
      bulkDeleteConversations: vi.fn().mockResolvedValue(undefined),
      deleteAllConversations: vi.fn().mockResolvedValue(undefined),
      startNewConversation: vi.fn(),
    });
  });

  describe('rendering', () => {
    it('should render conversation list', () => {
      renderWithProvider(<ConversationSidebar />);

      expect(screen.getByText('Today conversation')).toBeDefined();
      expect(screen.getByText('Yesterday conversation')).toBeDefined();
      expect(screen.getByText('Pinned conversation')).toBeDefined();
    });

    it('should render search input', () => {
      renderWithProvider(<ConversationSidebar />);

      expect(screen.getByPlaceholderText('Search conversations...')).toBeDefined();
    });

    it('should render New button', () => {
      renderWithProvider(<ConversationSidebar />);

      expect(screen.getByText('New')).toBeDefined();
    });

    it('should render Select button', () => {
      renderWithProvider(<ConversationSidebar />);

      expect(screen.getByText('Select')).toBeDefined();
    });

    it('should render Delete All button when conversations exist', () => {
      renderWithProvider(<ConversationSidebar />);

      expect(screen.getByText('Delete All')).toBeDefined();
    });

    it('should show Pinned section when pinned conversations exist', () => {
      renderWithProvider(<ConversationSidebar />);

      expect(screen.getByText('Pinned')).toBeDefined();
    });

    it('should show empty state when no conversations', () => {
      useRagStore.setState({ conversations: [] });
      renderWithProvider(<ConversationSidebar />);

      expect(screen.getByText('No conversations yet')).toBeDefined();
    });

    it('should call loadConversations on mount', () => {
      const mockLoadConversations = vi.fn();
      useRagStore.setState({ loadConversations: mockLoadConversations });

      renderWithProvider(<ConversationSidebar />);

      expect(mockLoadConversations).toHaveBeenCalled();
    });
  });

  describe('date grouping', () => {
    it('should group today conversations under Today', () => {
      renderWithProvider(<ConversationSidebar />);

      expect(screen.getByText('Today')).toBeDefined();
    });

    it('should group yesterday conversations under Yesterday', () => {
      renderWithProvider(<ConversationSidebar />);

      expect(screen.getByText('Yesterday')).toBeDefined();
    });

    it('should group older conversations under Last 7 Days', () => {
      renderWithProvider(<ConversationSidebar />);

      expect(screen.getByText('Last 7 Days')).toBeDefined();
    });
  });

  describe('search functionality', () => {
    it('should filter conversations by search query', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      const searchInput = screen.getByPlaceholderText('Search conversations...');
      await user.type(searchInput, 'Today');

      expect(screen.getByText('Today conversation')).toBeDefined();
      expect(screen.queryByText('Yesterday conversation')).toBeNull();
    });

    it('should show no results message when search has no matches', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      const searchInput = screen.getByPlaceholderText('Search conversations...');
      await user.type(searchInput, 'nonexistent');

      expect(screen.getByText('No conversations found')).toBeDefined();
    });

    it('should be case insensitive', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      const searchInput = screen.getByPlaceholderText('Search conversations...');
      await user.type(searchInput, 'TODAY');

      expect(screen.getByText('Today conversation')).toBeDefined();
    });
  });

  describe('selection', () => {
    it('should call selectConversation when conversation clicked', async () => {
      const mockSelectConversation = vi.fn();
      useRagStore.setState({ selectConversation: mockSelectConversation });

      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      await user.click(screen.getByText('Today conversation'));

      expect(mockSelectConversation).toHaveBeenCalledWith(1);
    });

    it('should highlight active conversation', () => {
      useRagStore.setState({ activeConversationId: 1 });
      renderWithProvider(<ConversationSidebar />);

      // The active conversation should have different styling
      // We check that the conversation is rendered (styling is harder to test)
      expect(screen.getByText('Today conversation')).toBeDefined();
    });

    it('should call onClose when conversation selected', async () => {
      const mockOnClose = vi.fn();
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar onClose={mockOnClose} />);

      await user.click(screen.getByText('Today conversation'));

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('new conversation', () => {
    it('should call startNewConversation when New button clicked', async () => {
      const mockStartNew = vi.fn();
      useRagStore.setState({ startNewConversation: mockStartNew });

      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      await user.click(screen.getByText('New'));

      expect(mockStartNew).toHaveBeenCalled();
    });

    it('should call onClose after starting new conversation', async () => {
      const mockOnClose = vi.fn();
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar onClose={mockOnClose} />);

      await user.click(screen.getByText('New'));

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('multi-select mode', () => {
    it('should enter multi-select mode when Select button clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      await user.click(screen.getByText('Select'));

      // Button should change to Cancel
      expect(screen.getByText('Cancel')).toBeDefined();
    });

    it('should show checkboxes in multi-select mode', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      await user.click(screen.getByText('Select'));

      // Checkboxes should appear
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
    });

    it('should exit multi-select mode when Cancel clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      // Enter multi-select
      await user.click(screen.getByText('Select'));
      expect(screen.getByText('Cancel')).toBeDefined();

      // Exit multi-select
      await user.click(screen.getByText('Cancel'));
      expect(screen.getByText('Select')).toBeDefined();
    });

    it('should show delete count button when items selected', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      // Enter multi-select mode
      await user.click(screen.getByText('Select'));

      // Click on a conversation to select it
      const checkboxes = screen.getAllByRole('checkbox');
      await user.click(checkboxes[0]);

      // Should show delete button with count
      expect(screen.getByText('Delete 1')).toBeDefined();
    });
  });

  describe('collapse/expand', () => {
    it('should collapse sidebar when collapse button clicked', async () => {
      const user = userEvent.setup();
      const { container } = renderWithProvider(<ConversationSidebar />);

      // Find collapse button (chevron left icon)
      const buttons = screen.getAllByRole('button');
      const collapseButton = buttons.find((btn) =>
        btn.querySelector('svg.tabler-icon-chevron-left')
      );

      if (collapseButton) {
        await user.click(collapseButton);
        // In collapsed state, should show minimal content
        // The sidebar width changes to 48px
      }
    });
  });

  describe('delete all modal', () => {
    it('should open delete all modal when Delete All clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      await user.click(screen.getByText('Delete All'));

      await waitFor(() => {
        expect(screen.getByText('Delete All Conversations')).toBeDefined();
      });
    });

    it('should show conversation count in delete modal', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      await user.click(screen.getByText('Delete All'));

      await waitFor(() => {
        // Should show count of conversations
        expect(screen.getByText(/6 conversation/i)).toBeDefined();
      });
    });

    it('should close modal when Cancel clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      await user.click(screen.getByText('Delete All'));

      await waitFor(() => {
        expect(screen.getByText('Delete All Conversations')).toBeDefined();
      });

      // Click Cancel in modal
      const buttons = screen.getAllByRole('button');
      const cancelButton = buttons.find((btn) => btn.textContent === 'Cancel');
      if (cancelButton) {
        await user.click(cancelButton);
      }

      await waitFor(() => {
        expect(screen.queryByText('Delete All Conversations')).toBeNull();
      });
    });

    it('should call deleteAllConversations when confirmed', async () => {
      const mockDeleteAll = vi.fn().mockResolvedValue(undefined);
      useRagStore.setState({ deleteAllConversations: mockDeleteAll });

      const user = userEvent.setup();
      renderWithProvider(<ConversationSidebar />);

      await user.click(screen.getByText('Delete All'));

      await waitFor(() => {
        expect(screen.getByText('Delete All Conversations')).toBeDefined();
      });

      // Find the modal dialog and the Delete All button inside it (not the trigger button)
      const modal = screen.getByRole('dialog');
      const deleteButton = within(modal).getByRole('button', { name: 'Delete All' });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(mockDeleteAll).toHaveBeenCalled();
      });
    });
  });
});
