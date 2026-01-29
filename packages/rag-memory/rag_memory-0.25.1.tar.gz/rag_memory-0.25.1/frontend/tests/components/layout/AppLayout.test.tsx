/**
 * AppLayout Component Tests
 *
 * Tests the main layout component with navigation.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import { AppLayout } from '../../../src/rag/components/layout/AppLayout';
import { useRagStore } from '../../../src/rag/store';

// Mock child components to isolate AppLayout testing
vi.mock('../../../src/rag/components/layout/TopBar', () => ({
  TopBar: () => <div data-testid="top-bar">TopBar</div>,
}));

vi.mock('../../../src/rag/components/layout/LeftNavigation', () => ({
  LeftNavigation: ({
    activeView,
    onViewChange,
  }: {
    activeView: string;
    onViewChange: (view: string) => void;
  }) => (
    <div data-testid="left-navigation">
      <span data-testid="active-view">{activeView}</span>
      <button onClick={() => onViewChange('collections')}>Go to Collections</button>
      <button onClick={() => onViewChange('chat')}>Go to Chat</button>
    </div>
  ),
}));

vi.mock('../../../src/rag/components/layout/MainContent', () => ({
  MainContent: ({ activeView }: { activeView: string }) => (
    <div data-testid="main-content">View: {activeView}</div>
  ),
}));

vi.mock('../../../src/rag/components/modals/IngestionModal', () => ({
  IngestionModal: ({
    opened,
    onClose,
  }: {
    opened: boolean;
    onClose: () => void;
  }) =>
    opened ? (
      <div data-testid="ingestion-modal">
        <button onClick={onClose}>Close</button>
      </div>
    ) : null,
}));

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('AppLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useRagStore.setState({
      ingestionModalOpen: false,
      ingestionModalTab: 'text',
      ingestionModalParams: {},
      closeIngestionModal: vi.fn(),
      loadCollections: vi.fn(),
    });
  });

  describe('rendering', () => {
    it('should render without crashing', () => {
      const { container } = renderWithProvider(<AppLayout />);
      expect(container).toBeDefined();
    });

    it('should render TopBar', () => {
      renderWithProvider(<AppLayout />);
      expect(screen.getByTestId('top-bar')).toBeDefined();
    });

    it('should render LeftNavigation', () => {
      renderWithProvider(<AppLayout />);
      expect(screen.getByTestId('left-navigation')).toBeDefined();
    });

    it('should render MainContent', () => {
      renderWithProvider(<AppLayout />);
      expect(screen.getByTestId('main-content')).toBeDefined();
    });

    it('should start with dashboard view', () => {
      renderWithProvider(<AppLayout />);
      expect(screen.getByTestId('active-view').textContent).toBe('dashboard');
      expect(screen.getByText('View: dashboard')).toBeDefined();
    });
  });

  describe('navigation', () => {
    it('should change view when navigation callback called', async () => {
      const user = userEvent.setup();
      renderWithProvider(<AppLayout />);

      await user.click(screen.getByText('Go to Collections'));

      expect(screen.getByTestId('active-view').textContent).toBe('collections');
      expect(screen.getByText('View: collections')).toBeDefined();
    });

    it('should switch to chat view', async () => {
      const user = userEvent.setup();
      renderWithProvider(<AppLayout />);

      await user.click(screen.getByText('Go to Chat'));

      expect(screen.getByTestId('active-view').textContent).toBe('chat');
      expect(screen.getByText('View: chat')).toBeDefined();
    });
  });

  describe('ingestion modal', () => {
    it('should not show ingestion modal when closed', () => {
      renderWithProvider(<AppLayout />);
      expect(screen.queryByTestId('ingestion-modal')).toBeNull();
    });

    it('should show ingestion modal when opened', () => {
      useRagStore.setState({
        ingestionModalOpen: true,
        ingestionModalTab: 'text',
        ingestionModalParams: {},
        closeIngestionModal: vi.fn(),
        loadCollections: vi.fn(),
      });

      renderWithProvider(<AppLayout />);
      expect(screen.getByTestId('ingestion-modal')).toBeDefined();
    });

    it('should close modal and refresh collections when modal closed', async () => {
      const mockCloseModal = vi.fn();
      const mockLoadCollections = vi.fn();
      useRagStore.setState({
        ingestionModalOpen: true,
        ingestionModalTab: 'text',
        ingestionModalParams: {},
        closeIngestionModal: mockCloseModal,
        loadCollections: mockLoadCollections,
      });

      const user = userEvent.setup();
      renderWithProvider(<AppLayout />);

      await user.click(screen.getByText('Close'));

      await waitFor(() => {
        expect(mockCloseModal).toHaveBeenCalled();
        expect(mockLoadCollections).toHaveBeenCalled();
      });
    });
  });
});
