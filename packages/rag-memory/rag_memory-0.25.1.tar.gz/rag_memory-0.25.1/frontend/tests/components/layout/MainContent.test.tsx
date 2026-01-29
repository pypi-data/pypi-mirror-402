/**
 * MainContent Component Tests
 *
 * Tests the view router that displays different components based on activeView.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { MainContent } from '../../../src/rag/components/layout/MainContent';
import { useRagStore } from '../../../src/rag/store';

// Mock child components to simplify testing
vi.mock('../../../src/rag/components/CollectionBrowser', () => ({
  default: () => <div data-testid="collection-browser">CollectionBrowser</div>,
}));

vi.mock('../../../src/rag/components/MessageList', () => ({
  default: () => <div data-testid="message-list">MessageList</div>,
}));

vi.mock('../../../src/rag/components/ChatInput', () => ({
  default: () => <div data-testid="chat-input">ChatInput</div>,
}));

vi.mock('../../../src/rag/components/StarterPrompts', () => ({
  default: () => <div data-testid="starter-prompts">StarterPrompts</div>,
}));

vi.mock('../../../src/rag/components/views/DocumentsView', () => ({
  DocumentsView: () => <div data-testid="documents-view">DocumentsView</div>,
}));

vi.mock('../../../src/rag/components/views/SearchView', () => ({
  SearchView: () => <div data-testid="search-view">SearchView</div>,
}));

vi.mock('../../../src/rag/components/dashboard', () => ({
  DashboardView: () => <div data-testid="dashboard-view">DashboardView</div>,
}));

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('MainContent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useRagStore.setState({ messages: [] });
  });

  describe('view routing', () => {
    it('should render DashboardView when activeView is dashboard', () => {
      renderWithProvider(<MainContent activeView="dashboard" />);

      expect(screen.getByTestId('dashboard-view')).toBeDefined();
    });

    it('should render CollectionBrowser when activeView is collections', () => {
      renderWithProvider(<MainContent activeView="collections" />);

      expect(screen.getByTestId('collection-browser')).toBeDefined();
    });

    it('should render DocumentsView when activeView is documents', () => {
      renderWithProvider(<MainContent activeView="documents" />);

      expect(screen.getByTestId('documents-view')).toBeDefined();
    });

    it('should render SearchView when activeView is search', () => {
      renderWithProvider(<MainContent activeView="search" />);

      expect(screen.getByTestId('search-view')).toBeDefined();
    });

    it('should render chat components when activeView is chat', () => {
      renderWithProvider(<MainContent activeView="chat" />);

      expect(screen.getByTestId('chat-input')).toBeDefined();
    });
  });

  describe('chat view behavior', () => {
    it('should show StarterPrompts when no messages exist', () => {
      useRagStore.setState({ messages: [] });

      renderWithProvider(<MainContent activeView="chat" />);

      expect(screen.getByTestId('starter-prompts')).toBeDefined();
      expect(screen.queryByTestId('message-list')).toBeNull();
    });

    it('should show MessageList when messages exist', () => {
      useRagStore.setState({
        messages: [
          {
            id: '1',
            role: 'user',
            content: 'Hello',
            createdAt: new Date().toISOString(),
            toolExecutions: [],
          },
        ],
      });

      renderWithProvider(<MainContent activeView="chat" />);

      expect(screen.getByTestId('message-list')).toBeDefined();
      expect(screen.queryByTestId('starter-prompts')).toBeNull();
    });

    it('should always show ChatInput in chat view', () => {
      renderWithProvider(<MainContent activeView="chat" />);

      expect(screen.getByTestId('chat-input')).toBeDefined();
    });
  });

  describe('view exclusivity', () => {
    it('should only render one view at a time', () => {
      renderWithProvider(<MainContent activeView="search" />);

      expect(screen.getByTestId('search-view')).toBeDefined();
      expect(screen.queryByTestId('dashboard-view')).toBeNull();
      expect(screen.queryByTestId('collection-browser')).toBeNull();
      expect(screen.queryByTestId('documents-view')).toBeNull();
      expect(screen.queryByTestId('chat-input')).toBeNull();
    });
  });
});
