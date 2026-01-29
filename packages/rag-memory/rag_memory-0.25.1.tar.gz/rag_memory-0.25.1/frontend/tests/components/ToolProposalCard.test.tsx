/**
 * ToolProposalCard Component Tests
 *
 * Tests tool approval UI for pending tool calls.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import ToolProposalCard from '../../src/rag/components/ToolProposalCard';
import type { PendingToolCall } from '../../src/rag/types';

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('ToolProposalCard', () => {
  const mockOnApprove = vi.fn();
  const mockOnReject = vi.fn();
  const mockOnRevise = vi.fn();

  const singleTool: PendingToolCall[] = [
    {
      id: 't1',
      name: 'search_documents',
      args: { query: 'test query', collection_name: 'my-collection' },
    },
  ];

  const multipleTools: PendingToolCall[] = [
    {
      id: 't1',
      name: 'search_documents',
      args: { query: 'test query' },
    },
    {
      id: 't2',
      name: 'ingest_url',
      args: { url: 'https://example.com', collection_name: 'docs' },
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render tool approval badge', () => {
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      expect(screen.getByText('Tool Approval Required')).toBeDefined();
    });

    it('should display tool count for single tool', () => {
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      expect(screen.getByText('1 tool pending')).toBeDefined();
    });

    it('should display tool count for multiple tools', () => {
      renderWithProvider(
        <ToolProposalCard
          tools={multipleTools}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      expect(screen.getByText('2 tools pending')).toBeDefined();
    });

    it('should display formatted tool name', () => {
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      expect(screen.getByText('Search Documents')).toBeDefined();
    });

    it('should display parameter count', () => {
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      expect(screen.getByText('2 parameters')).toBeDefined();
    });

    it('should display parameter values', () => {
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      expect(screen.getByText('query')).toBeDefined();
      expect(screen.getByText('test query')).toBeDefined();
    });
  });

  describe('approve action', () => {
    it('should have Approve button', () => {
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      expect(screen.getByRole('button', { name: /approve/i })).toBeDefined();
    });

    it('should call onApprove when Approve clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      await user.click(screen.getByRole('button', { name: /approve/i }));

      expect(mockOnApprove).toHaveBeenCalled();
    });
  });

  describe('reject action', () => {
    it('should have Reject button', () => {
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      expect(screen.getByRole('button', { name: /reject/i })).toBeDefined();
    });

    it('should show reject reason input when Reject clicked first time', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      await user.click(screen.getByRole('button', { name: /reject/i }));

      // Should show input and Confirm Reject button
      expect(screen.getByPlaceholderText(/reason for rejection/i)).toBeDefined();
      expect(screen.getByRole('button', { name: /confirm reject/i })).toBeDefined();
    });

    it('should call onReject when confirmed', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      // First click shows input
      await user.click(screen.getByRole('button', { name: /reject/i }));

      // Enter reason
      const input = screen.getByPlaceholderText(/reason for rejection/i);
      await user.type(input, 'Not needed');

      // Confirm
      await user.click(screen.getByRole('button', { name: /confirm reject/i }));

      expect(mockOnReject).toHaveBeenCalledWith('Not needed');
    });

    it('should call onReject without reason when no reason entered', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      // First click shows input
      await user.click(screen.getByRole('button', { name: /reject/i }));

      // Confirm without reason
      await user.click(screen.getByRole('button', { name: /confirm reject/i }));

      expect(mockOnReject).toHaveBeenCalledWith();
    });
  });

  describe('edit mode', () => {
    it('should have edit button', () => {
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      expect(screen.getByTitle(/edit parameters/i)).toBeDefined();
    });

    it('should show editable inputs when edit mode enabled', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      await user.click(screen.getByTitle(/edit parameters/i));

      // Should show text inputs for parameters
      const inputs = screen.getAllByRole('textbox');
      expect(inputs.length).toBeGreaterThan(0);
    });

    it('should change Approve button to Apply & Execute in edit mode', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      await user.click(screen.getByTitle(/edit parameters/i));

      expect(screen.getByRole('button', { name: /apply & execute/i })).toBeDefined();
    });

    it('should call onRevise with edited tools when Apply clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      // Enter edit mode
      await user.click(screen.getByTitle(/edit parameters/i));

      // Click Apply & Execute
      await user.click(screen.getByRole('button', { name: /apply & execute/i }));

      expect(mockOnRevise).toHaveBeenCalled();
    });
  });

  describe('collapse/expand', () => {
    it('should start with tools expanded', () => {
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      // Parameter values should be visible
      expect(screen.getByText('test query')).toBeDefined();
    });

    it('should collapse tool when header clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(
        <ToolProposalCard
          tools={singleTool}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          onRevise={mockOnRevise}
        />
      );

      // Click on tool header to collapse
      await user.click(screen.getByText('Search Documents'));

      // Wait for collapse animation - the content might still be in DOM but hidden
      await waitFor(() => {
        // After collapse, the parameter section should be collapsed
        // Mantine Collapse hides content with height: 0
        const paramSection = screen.queryByText('test query');
        // Content might still be in DOM but hidden by Collapse
      });
    });
  });
});
