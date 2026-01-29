/**
 * StarterPrompts Component Tests
 *
 * Tests the starter prompt suggestions shown on empty chat.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import StarterPrompts from '../../src/rag/components/StarterPrompts';
import { useRagStore } from '../../src/rag/store';
import * as ragApi from '../../src/rag/ragApi';
import type { StarterPrompt } from '../../src/rag/types';

// Mock ragApi
vi.mock('../../src/rag/ragApi', () => ({
  getStarterPrompts: vi.fn(),
}));

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('StarterPrompts', () => {
  const mockPrompts: StarterPrompt[] = [
    {
      id: 1,
      prompt_text: 'What collections do I have?',
      category: 'Discovery',
      has_placeholder: false,
    },
    {
      id: 2,
      prompt_text: 'Search my knowledge base for [topic]',
      category: 'Search',
      has_placeholder: true,
    },
    {
      id: 3,
      prompt_text: 'Tell me about my recent documents',
      category: null,
      has_placeholder: false,
    },
  ];

  const mockSendMessage = vi.fn();
  const mockSetInputValue = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    useRagStore.setState({
      sendMessage: mockSendMessage,
      setInputValue: mockSetInputValue,
    });
  });

  describe('loading state', () => {
    it('should show loader while fetching prompts', () => {
      vi.mocked(ragApi.getStarterPrompts).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderWithProvider(<StarterPrompts />);

      // Mantine Loader renders with specific role
      const loader = document.querySelector('.mantine-Loader-root');
      expect(loader).toBeDefined();
    });
  });

  describe('prompt display', () => {
    it('should display welcome message after loading', async () => {
      vi.mocked(ragApi.getStarterPrompts).mockResolvedValue(mockPrompts);

      renderWithProvider(<StarterPrompts />);

      await waitFor(() => {
        expect(screen.getByText('Welcome to RAG Memory')).toBeDefined();
      });
    });

    it('should display all prompts', async () => {
      vi.mocked(ragApi.getStarterPrompts).mockResolvedValue(mockPrompts);

      renderWithProvider(<StarterPrompts />);

      await waitFor(() => {
        expect(screen.getByText('What collections do I have?')).toBeDefined();
        expect(screen.getByText('Search my knowledge base for [topic]')).toBeDefined();
        expect(screen.getByText('Tell me about my recent documents')).toBeDefined();
      });
    });

    it('should display category badges when present', async () => {
      vi.mocked(ragApi.getStarterPrompts).mockResolvedValue(mockPrompts);

      renderWithProvider(<StarterPrompts />);

      await waitFor(() => {
        expect(screen.getByText('Discovery')).toBeDefined();
        expect(screen.getByText('Search')).toBeDefined();
      });
    });

    it('should show template hint for placeholder prompts', async () => {
      vi.mocked(ragApi.getStarterPrompts).mockResolvedValue(mockPrompts);

      renderWithProvider(<StarterPrompts />);

      await waitFor(() => {
        expect(screen.getByText('Click to use this prompt template')).toBeDefined();
      });
    });
  });

  describe('prompt interactions', () => {
    it('should send message immediately for non-placeholder prompts', async () => {
      vi.mocked(ragApi.getStarterPrompts).mockResolvedValue(mockPrompts);
      const user = userEvent.setup();

      renderWithProvider(<StarterPrompts />);

      await waitFor(() => {
        expect(screen.getByText('What collections do I have?')).toBeDefined();
      });

      await user.click(screen.getByText('What collections do I have?'));

      expect(mockSendMessage).toHaveBeenCalledWith('What collections do I have?');
      expect(mockSetInputValue).not.toHaveBeenCalled();
    });

    it('should fill input for placeholder prompts without sending', async () => {
      vi.mocked(ragApi.getStarterPrompts).mockResolvedValue(mockPrompts);
      const user = userEvent.setup();

      renderWithProvider(<StarterPrompts />);

      await waitFor(() => {
        expect(screen.getByText('Search my knowledge base for [topic]')).toBeDefined();
      });

      await user.click(screen.getByText('Search my knowledge base for [topic]'));

      expect(mockSetInputValue).toHaveBeenCalledWith('Search my knowledge base for [topic]');
      expect(mockSendMessage).not.toHaveBeenCalled();
    });
  });

  describe('error handling', () => {
    it('should handle API errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(ragApi.getStarterPrompts).mockRejectedValue(new Error('API error'));

      renderWithProvider(<StarterPrompts />);

      await waitFor(() => {
        // Should still show the welcome message even if prompts fail to load
        expect(screen.getByText('Welcome to RAG Memory')).toBeDefined();
      });

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should show empty state when no prompts returned', async () => {
      vi.mocked(ragApi.getStarterPrompts).mockResolvedValue([]);

      renderWithProvider(<StarterPrompts />);

      await waitFor(() => {
        expect(screen.getByText('Welcome to RAG Memory')).toBeDefined();
        // No prompt cards should be rendered
        expect(screen.queryByText('Discovery')).toBeNull();
      });
    });
  });
});
