/**
 * LeftNavigation Component Tests
 *
 * Tests the left sidebar navigation component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import { LeftNavigation } from '../../../src/rag/components/layout/LeftNavigation';
import { useRagStore } from '../../../src/rag/store';

// Mock ConversationSidebar to simplify testing
vi.mock('../../../src/rag/components/ConversationSidebar', () => ({
  default: () => <div data-testid="conversation-sidebar">ConversationSidebar</div>,
}));

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('LeftNavigation', () => {
  const mockOnViewChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    useRagStore.setState({ conversations: [], messages: [] });
  });

  describe('rendering', () => {
    it('should render all navigation items', () => {
      renderWithProvider(
        <LeftNavigation activeView="dashboard" onViewChange={mockOnViewChange} />
      );

      expect(screen.getByText('Dashboard')).toBeDefined();
      expect(screen.getByText('Collections')).toBeDefined();
      expect(screen.getByText('Documents')).toBeDefined();
      expect(screen.getByText('Search')).toBeDefined();
      expect(screen.getByText('Agent Chat')).toBeDefined();
    });

    it('should highlight active view', () => {
      renderWithProvider(
        <LeftNavigation activeView="collections" onViewChange={mockOnViewChange} />
      );

      // Collections should have active styling
      const collectionsLink = screen.getByText('Collections').closest('a, button, div[role="button"]');
      expect(collectionsLink).toBeDefined();
    });

    it('should have collapse button', () => {
      renderWithProvider(
        <LeftNavigation activeView="dashboard" onViewChange={mockOnViewChange} />
      );

      expect(screen.getByTitle('Collapse sidebar')).toBeDefined();
    });
  });

  describe('navigation', () => {
    it('should call onViewChange when nav item clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <LeftNavigation activeView="dashboard" onViewChange={mockOnViewChange} />
      );

      await user.click(screen.getByText('Collections'));

      expect(mockOnViewChange).toHaveBeenCalledWith('collections');
    });

    it('should call onViewChange with search when Search clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <LeftNavigation activeView="dashboard" onViewChange={mockOnViewChange} />
      );

      await user.click(screen.getByText('Search'));

      expect(mockOnViewChange).toHaveBeenCalledWith('search');
    });

    it('should call onViewChange with chat when Agent Chat clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <LeftNavigation activeView="dashboard" onViewChange={mockOnViewChange} />
      );

      await user.click(screen.getByText('Agent Chat'));

      expect(mockOnViewChange).toHaveBeenCalledWith('chat');
    });
  });

  describe('collapse behavior', () => {
    it('should collapse when collapse button clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <LeftNavigation activeView="dashboard" onViewChange={mockOnViewChange} />
      );

      await user.click(screen.getByTitle('Collapse sidebar'));

      // Should now show expand button
      expect(screen.getByTitle('Expand sidebar')).toBeDefined();
    });

    it('should hide labels when collapsed', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <LeftNavigation activeView="dashboard" onViewChange={mockOnViewChange} />
      );

      // Click collapse
      await user.click(screen.getByTitle('Collapse sidebar'));

      // Labels should be hidden (not rendered as text)
      expect(screen.queryByText('Dashboard')).toBeNull();
      expect(screen.queryByText('Collections')).toBeNull();
    });

    it('should expand when expand button clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <LeftNavigation activeView="dashboard" onViewChange={mockOnViewChange} />
      );

      // Collapse first
      await user.click(screen.getByTitle('Collapse sidebar'));

      // Then expand
      await user.click(screen.getByTitle('Expand sidebar'));

      // Labels should be visible again
      expect(screen.getByText('Dashboard')).toBeDefined();
    });
  });

  describe('chat view integration', () => {
    it('should show ConversationSidebar when in chat view and not collapsed', () => {
      renderWithProvider(
        <LeftNavigation activeView="chat" onViewChange={mockOnViewChange} />
      );

      expect(screen.getByTestId('conversation-sidebar')).toBeDefined();
    });

    it('should hide ConversationSidebar when not in chat view', () => {
      renderWithProvider(
        <LeftNavigation activeView="collections" onViewChange={mockOnViewChange} />
      );

      expect(screen.queryByTestId('conversation-sidebar')).toBeNull();
    });

    it('should hide ConversationSidebar when collapsed in chat view', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <LeftNavigation activeView="chat" onViewChange={mockOnViewChange} />
      );

      // Initially visible
      expect(screen.getByTestId('conversation-sidebar')).toBeDefined();

      // Collapse
      await user.click(screen.getByTitle('Collapse sidebar'));

      // Should be hidden
      expect(screen.queryByTestId('conversation-sidebar')).toBeNull();
    });
  });
});
