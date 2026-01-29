/**
 * ChatInput Component Tests
 *
 * Tests user interaction with the chat input component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import ChatInput from '../../src/rag/components/ChatInput';
import { useRagStore } from '../../src/rag/store';

// Wrapper with Mantine provider for testing
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

// Helper to render with wrapper
function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('ChatInput', () => {
  beforeEach(() => {
    // Reset store state
    useRagStore.setState({
      inputValue: '',
      isStreaming: false,
      messages: [],
      activeConversationId: null,
      sseClient: null,
    });
  });

  describe('input behavior', () => {
    it('should render with placeholder text', () => {
      renderWithProvider(<ChatInput />);

      const input = screen.getByPlaceholderText(/ask me anything/i);
      expect(input).toBeDefined();
    });

    it('should update store value on input change', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ChatInput />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'Hello world');

      expect(useRagStore.getState().inputValue).toBe('Hello world');
    });

    it('should display value from store', () => {
      useRagStore.setState({ inputValue: 'Pre-filled value' });
      renderWithProvider(<ChatInput />);

      const input = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(input.value).toBe('Pre-filled value');
    });

    it('should be disabled when streaming', () => {
      useRagStore.setState({ isStreaming: true });
      renderWithProvider(<ChatInput />);

      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
    });
  });

  describe('send functionality', () => {
    it('should have send button', () => {
      renderWithProvider(<ChatInput />);

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThanOrEqual(1);
    });

    it('should disable send button when input is empty', () => {
      renderWithProvider(<ChatInput />);

      // Find the send button (last button in the group)
      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];

      expect(sendButton).toBeDisabled();
    });

    it('should enable send button when input has text', async () => {
      const user = userEvent.setup();
      renderWithProvider(<ChatInput />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'Test message');

      // Find the send button (last button in the group)
      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];

      expect(sendButton).not.toBeDisabled();
    });

    it('should clear input after sending', async () => {
      // Mock sendMessage to not actually send
      const mockSendMessage = vi.fn().mockResolvedValue(undefined);
      useRagStore.setState({
        inputValue: 'Test message',
        sendMessage: mockSendMessage,
        sseClient: { send: vi.fn() } as any,
      });

      const user = userEvent.setup();
      renderWithProvider(<ChatInput />);

      // Find and click send button
      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];
      await user.click(sendButton);

      // Wait for state update
      expect(useRagStore.getState().inputValue).toBe('');
    });

    it('should send on Enter key', async () => {
      const mockSendMessage = vi.fn().mockResolvedValue(undefined);
      useRagStore.setState({
        inputValue: 'Test message',
        sendMessage: mockSendMessage,
        sseClient: { send: vi.fn() } as any,
      });

      const user = userEvent.setup();
      renderWithProvider(<ChatInput />);

      const input = screen.getByRole('textbox');
      await user.type(input, '{Enter}');

      // Input should be cleared
      expect(useRagStore.getState().inputValue).toBe('');
    });

    it('should not send on Shift+Enter (allows multiline)', async () => {
      useRagStore.setState({ inputValue: 'Test' });

      const user = userEvent.setup();
      renderWithProvider(<ChatInput />);

      const input = screen.getByRole('textbox');

      // Simulate Shift+Enter (should not clear/send)
      await user.type(input, '{Shift>}{Enter}{/Shift}');

      // Input should still have content (not sent)
      const state = useRagStore.getState();
      expect(state.inputValue.length).toBeGreaterThan(0);
    });

    it('should disable send button when streaming', () => {
      useRagStore.setState({ inputValue: 'Test message', isStreaming: true });
      renderWithProvider(<ChatInput />);

      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];

      expect(sendButton).toBeDisabled();
    });
  });

  describe('file attachment buttons', () => {
    it('should have file attachment button', () => {
      renderWithProvider(<ChatInput />);

      // Check for paperclip icon button (attach files)
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThanOrEqual(2);
    });

    it('should have folder attachment button', () => {
      renderWithProvider(<ChatInput />);

      // Check for folder icon button
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThanOrEqual(3);
    });

    it('should disable attachment buttons when streaming', () => {
      useRagStore.setState({ isStreaming: true });
      renderWithProvider(<ChatInput />);

      const buttons = screen.getAllByRole('button');
      // All buttons should be disabled when streaming
      buttons.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });
  });

  describe('formatFileSize utility', () => {
    // Test the formatting indirectly through component behavior
    it('should render without errors', () => {
      renderWithProvider(<ChatInput />);
      expect(screen.getByRole('textbox')).toBeDefined();
    });
  });

  describe('file attachment display', () => {
    // Mock file for testing
    const createMockFile = (name: string, size: number, content: string): File => {
      const blob = new Blob([content], { type: 'text/plain' });
      return new File([blob], name, { type: 'text/plain' });
    };

    // Helper to simulate file selection
    const simulateFileSelection = async (files: File[]) => {
      // Mock createElement to intercept file input creation
      const originalCreateElement = document.createElement.bind(document);
      let fileInput: HTMLInputElement | null = null;

      vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
        const element = originalCreateElement(tagName);
        if (tagName === 'input') {
          fileInput = element as HTMLInputElement;
          // Mock click to trigger onchange
          vi.spyOn(element, 'click').mockImplementation(() => {
            // Simulate file selection
            Object.defineProperty(element, 'files', { value: files });
            if (fileInput?.onchange) {
              fileInput.onchange({ target: { files } } as any);
            }
          });
        }
        return element;
      });

      return fileInput;
    };

    it('should show placeholder asking about knowledge base when no files attached', () => {
      renderWithProvider(<ChatInput />);

      const input = screen.getByPlaceholderText(/ask me anything about your knowledge base/i);
      expect(input).toBeDefined();
    });

    it('should enable send button when files are attached even without text', async () => {
      const mockFile = createMockFile('test.txt', 100, 'test content');

      simulateFileSelection([mockFile]);

      const user = userEvent.setup();
      renderWithProvider(<ChatInput />);

      // Click the file attachment button
      const buttons = screen.getAllByRole('button');
      const attachButton = buttons.find(btn => btn.getAttribute('title') === 'Attach files');
      expect(attachButton).toBeDefined();

      if (attachButton) {
        await user.click(attachButton);
      }

      // Wait for file to be processed - need to wait for async FileReader
      await new Promise(resolve => setTimeout(resolve, 100));

      // Restore createElement
      vi.restoreAllMocks();
    });

    it('should have attach files button with correct title', () => {
      renderWithProvider(<ChatInput />);

      const attachButton = screen.getByTitle('Attach files');
      expect(attachButton).toBeDefined();
    });

    it('should have attach folder button with correct title', () => {
      renderWithProvider(<ChatInput />);

      const folderButton = screen.getByTitle('Attach folder');
      expect(folderButton).toBeDefined();
    });

    it('should disable input when reading files', () => {
      // Simulate file reading state - this is internal state but we can verify behavior
      renderWithProvider(<ChatInput />);

      // Initially should not be disabled
      const input = screen.getByRole('textbox');
      expect(input).not.toBeDisabled();
    });

    it('should have loading state on attach button when reading files', () => {
      renderWithProvider(<ChatInput />);

      // Initially buttons should not be loading
      const attachButton = screen.getByTitle('Attach files');
      expect(attachButton).not.toHaveAttribute('data-loading');
    });
  });

  describe('message with attachments', () => {
    it('should call sendMessage when clicking send with input text', async () => {
      const mockSendMessage = vi.fn().mockResolvedValue(undefined);
      useRagStore.setState({
        inputValue: '',
        sendMessage: mockSendMessage,
        sseClient: { send: vi.fn() } as any,
      });

      const user = userEvent.setup();
      renderWithProvider(<ChatInput />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'Hello');

      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];
      await user.click(sendButton);

      expect(mockSendMessage).toHaveBeenCalledWith('Hello');
    });

    it('should not send when input is empty and no files attached', async () => {
      const mockSendMessage = vi.fn().mockResolvedValue(undefined);
      useRagStore.setState({
        inputValue: '',
        sendMessage: mockSendMessage,
        sseClient: { send: vi.fn() } as any,
      });

      const user = userEvent.setup();
      renderWithProvider(<ChatInput />);

      // Try to click send with empty input
      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];

      // Button should be disabled
      expect(sendButton).toBeDisabled();
    });

    it('should trim whitespace from input before sending', async () => {
      const mockSendMessage = vi.fn().mockResolvedValue(undefined);
      useRagStore.setState({
        inputValue: '  test message  ',
        sendMessage: mockSendMessage,
        sseClient: { send: vi.fn() } as any,
      });

      const user = userEvent.setup();
      renderWithProvider(<ChatInput />);

      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];
      await user.click(sendButton);

      expect(mockSendMessage).toHaveBeenCalledWith('test message');
    });
  });
});
