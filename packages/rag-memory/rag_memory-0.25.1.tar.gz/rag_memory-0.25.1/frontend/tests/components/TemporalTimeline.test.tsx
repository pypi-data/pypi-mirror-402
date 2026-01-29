/**
 * TemporalTimeline Component Tests
 *
 * Tests the temporal knowledge evolution timeline display.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import TemporalTimeline from '../../src/rag/components/TemporalTimeline';
import type { TemporalResult } from '../../src/rag/types';

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('TemporalTimeline', () => {
  const mockTimeline: TemporalResult[] = [
    {
      fact: 'Project started',
      relationship_type: 'INITIATED',
      valid_from: '2024-01-01T00:00:00Z',
      valid_until: null,
      status: 'current',
      created_at: '2024-01-01T00:00:00Z',
      expired_at: null,
    },
    {
      fact: 'Phase 1 completed',
      relationship_type: 'COMPLETED',
      valid_from: '2024-02-15T00:00:00Z',
      valid_until: '2024-03-01T00:00:00Z',
      status: 'superseded',
      created_at: '2024-02-15T00:00:00Z',
      expired_at: '2024-03-01T00:00:00Z',
    },
  ];

  describe('empty state', () => {
    it('should return null when timeline is undefined', () => {
      const { container } = renderWithProvider(
        <TemporalTimeline timeline={undefined as unknown as TemporalResult[]} />
      );
      expect(container.querySelector('.mantine-Card-root')).toBeNull();
    });

    it('should return null when timeline is empty', () => {
      const { container } = renderWithProvider(<TemporalTimeline timeline={[]} />);
      expect(container.querySelector('.mantine-Card-root')).toBeNull();
    });
  });

  describe('rendering', () => {
    it('should render timeline title', () => {
      renderWithProvider(<TemporalTimeline timeline={mockTimeline} />);
      expect(screen.getByText('Knowledge Evolution Timeline')).toBeDefined();
    });

    it('should display fact content', () => {
      renderWithProvider(<TemporalTimeline timeline={mockTimeline} />);
      expect(screen.getByText('Project started')).toBeDefined();
      expect(screen.getByText('Phase 1 completed')).toBeDefined();
    });

    it('should display relationship types', () => {
      renderWithProvider(<TemporalTimeline timeline={mockTimeline} />);
      expect(screen.getByText('INITIATED')).toBeDefined();
      expect(screen.getByText('COMPLETED')).toBeDefined();
    });

    it('should display status badges', () => {
      renderWithProvider(<TemporalTimeline timeline={mockTimeline} />);
      expect(screen.getByText('current')).toBeDefined();
      expect(screen.getByText('superseded')).toBeDefined();
    });

    it('should show Present for null valid_until', () => {
      renderWithProvider(<TemporalTimeline timeline={mockTimeline} />);
      expect(screen.getByText(/Present/)).toBeDefined();
    });

    it('should format dates correctly', () => {
      renderWithProvider(<TemporalTimeline timeline={mockTimeline} />);
      // Should contain formatted date strings
      const dateElements = screen.getAllByText(/\d{1,2}\/\d{1,2}\/\d{4}/);
      expect(dateElements.length).toBeGreaterThan(0);
    });
  });

  describe('sorting', () => {
    it('should sort timeline by valid_from date (most recent first)', () => {
      const unsortedTimeline: TemporalResult[] = [
        {
          fact: 'Old event',
          relationship_type: 'OLD',
          valid_from: '2023-01-01T00:00:00Z',
          valid_until: null,
          status: 'superseded',
          created_at: '2023-01-01T00:00:00Z',
          expired_at: null,
        },
        {
          fact: 'New event',
          relationship_type: 'NEW',
          valid_from: '2024-06-01T00:00:00Z',
          valid_until: null,
          status: 'current',
          created_at: '2024-06-01T00:00:00Z',
          expired_at: null,
        },
      ];

      renderWithProvider(<TemporalTimeline timeline={unsortedTimeline} />);

      // Get all fact elements and verify order
      const newEvent = screen.getByText('New event');
      const oldEvent = screen.getByText('Old event');

      // "New event" should appear before "Old event" in the DOM
      expect(
        newEvent.compareDocumentPosition(oldEvent) & Node.DOCUMENT_POSITION_FOLLOWING
      ).toBeTruthy();
    });
  });
});
