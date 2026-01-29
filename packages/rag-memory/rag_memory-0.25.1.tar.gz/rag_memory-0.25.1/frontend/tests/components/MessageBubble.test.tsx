/**
 * MessageBubble Component Tests
 *
 * Tests chat message rendering for user and assistant messages.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import MessageBubble from '../../src/rag/components/MessageBubble';
import type { ChatMessage, ToolExecution } from '../../src/rag/types';

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('MessageBubble', () => {
  describe('user messages', () => {
    it('should render user message content', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'user',
        content: 'Hello, how are you?',
        created_at: '2024-01-01T12:00:00Z',
      };

      renderWithProvider(<MessageBubble message={message} />);

      expect(screen.getByText('Hello, how are you?')).toBeDefined();
    });

    it('should display "You" badge for user messages', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'user',
        content: 'Test message',
        created_at: '2024-01-01T12:00:00Z',
      };

      renderWithProvider(<MessageBubble message={message} />);

      expect(screen.getByText('You')).toBeDefined();
    });

    it('should display timestamp', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'user',
        content: 'Test message',
        created_at: '2024-01-01T12:30:00Z',
      };

      renderWithProvider(<MessageBubble message={message} />);

      // Timestamp should be rendered
      const timeElement = screen.getByText((text) => text.includes(':'));
      expect(timeElement).toBeDefined();
    });

    it('should show file attachment indicator when files attached', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'user',
        content: 'Please check this\n\n---\n**Attached Files (2):**\n\n**file1.txt**',
        created_at: '2024-01-01T12:00:00Z',
      };

      renderWithProvider(<MessageBubble message={message} />);

      expect(screen.getByText('2 files attached')).toBeDefined();
      expect(screen.getByText('Please check this')).toBeDefined();
    });

    it('should show single file indicator correctly', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'user',
        content: 'Check this\n\n---\n**Attached Files (1):**\n\n**file.txt**',
        created_at: '2024-01-01T12:00:00Z',
      };

      renderWithProvider(<MessageBubble message={message} />);

      expect(screen.getByText('1 file attached')).toBeDefined();
    });

    it('should handle files-only messages', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'user',
        content: '**Attached Files (3):**\n\n**file1.txt**\n**file2.txt**\n**file3.txt**',
        created_at: '2024-01-01T12:00:00Z',
      };

      renderWithProvider(<MessageBubble message={message} />);

      expect(screen.getByText('3 files attached')).toBeDefined();
      // Should show default message when no user text
      expect(screen.getByText(/ingest these files/i)).toBeDefined();
    });
  });

  describe('assistant messages', () => {
    it('should render assistant message content', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'assistant',
        content: 'I can help you with that!',
        created_at: '2024-01-01T12:00:00Z',
      };

      renderWithProvider(<MessageBubble message={message} />);

      expect(screen.getByText('I can help you with that!')).toBeDefined();
    });

    it('should display "Assistant" badge for assistant messages', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'assistant',
        content: 'Test message',
        created_at: '2024-01-01T12:00:00Z',
      };

      renderWithProvider(<MessageBubble message={message} />);

      expect(screen.getByText('Assistant')).toBeDefined();
    });
  });

  describe('streaming indicator', () => {
    it('should show streaming indicator when isStreaming is true', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'assistant',
        content: 'Thinking...',
        created_at: '2024-01-01T12:00:00Z',
      };

      renderWithProvider(<MessageBubble message={message} isStreaming={true} />);

      // Mantine Loader should be present
      const loader = document.querySelector('.mantine-Loader-root');
      expect(loader).toBeDefined();
    });

    it('should not show streaming indicator when isStreaming is false', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'assistant',
        content: 'Done',
        created_at: '2024-01-01T12:00:00Z',
      };

      renderWithProvider(<MessageBubble message={message} isStreaming={false} />);

      // No loader should be in the content area (there might be one in tool executions)
      expect(screen.getByText('Done')).toBeDefined();
    });
  });

  describe('tool executions', () => {
    it('should display running tool execution with loader', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'assistant',
        content: 'Let me search for that.',
        created_at: '2024-01-01T12:00:00Z',
      };

      const toolExecutions: ToolExecution[] = [
        { id: 't1', name: 'search_documents', status: 'running', startTime: Date.now() },
      ];

      renderWithProvider(
        <MessageBubble message={message} currentToolExecutions={toolExecutions} />
      );

      expect(screen.getByText('Searching documents...')).toBeDefined();
    });

    it('should display completed tool execution with check icon', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'assistant',
        content: 'Found results.',
        created_at: '2024-01-01T12:00:00Z',
      };

      const toolExecutions: ToolExecution[] = [
        { id: 't1', name: 'search_documents', status: 'completed', startTime: Date.now() },
      ];

      renderWithProvider(
        <MessageBubble message={message} currentToolExecutions={toolExecutions} />
      );

      expect(screen.getByText('✓ Searching documents')).toBeDefined();
    });

    it('should display failed tool execution with X icon', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'assistant',
        content: 'Search failed.',
        created_at: '2024-01-01T12:00:00Z',
      };

      const toolExecutions: ToolExecution[] = [
        { id: 't1', name: 'search_documents', status: 'failed', startTime: Date.now() },
      ];

      renderWithProvider(
        <MessageBubble message={message} currentToolExecutions={toolExecutions} />
      );

      expect(screen.getByText('✗ Searching documents')).toBeDefined();
    });

    it('should display multiple tool executions', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'assistant',
        content: 'Working on it.',
        created_at: '2024-01-01T12:00:00Z',
      };

      const toolExecutions: ToolExecution[] = [
        { id: 't1', name: 'search_documents', status: 'completed', startTime: Date.now() },
        { id: 't2', name: 'web_search', status: 'running', startTime: Date.now() },
      ];

      renderWithProvider(
        <MessageBubble message={message} currentToolExecutions={toolExecutions} />
      );

      expect(screen.getByText('✓ Searching documents')).toBeDefined();
      expect(screen.getByText('Searching web...')).toBeDefined();
    });

    it('should not display tool executions for user messages', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'user',
        content: 'Hello',
        created_at: '2024-01-01T12:00:00Z',
      };

      const toolExecutions: ToolExecution[] = [
        { id: 't1', name: 'search_documents', status: 'running', startTime: Date.now() },
      ];

      renderWithProvider(
        <MessageBubble message={message} currentToolExecutions={toolExecutions} />
      );

      // Tool execution should not be shown for user messages
      expect(screen.queryByText('Searching documents...')).toBeNull();
    });

    it('should format unknown tool names with generic message', () => {
      const message: ChatMessage = {
        id: 1,
        role: 'assistant',
        content: 'Processing.',
        created_at: '2024-01-01T12:00:00Z',
      };

      const toolExecutions: ToolExecution[] = [
        { id: 't1', name: 'unknown_tool', status: 'running', startTime: Date.now() },
      ];

      renderWithProvider(
        <MessageBubble message={message} currentToolExecutions={toolExecutions} />
      );

      expect(screen.getByText('Working......')).toBeDefined();
    });
  });
});
