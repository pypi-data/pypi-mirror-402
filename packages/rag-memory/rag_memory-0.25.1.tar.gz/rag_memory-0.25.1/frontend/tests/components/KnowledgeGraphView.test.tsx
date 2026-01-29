/**
 * KnowledgeGraphView Component Tests
 *
 * Tests the knowledge graph relationships and temporal timeline display.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import KnowledgeGraphView from '../../src/rag/components/KnowledgeGraphView';

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('KnowledgeGraphView', () => {
  const mockRelationships = [
    {
      id: '1',
      relationship_type: 'BELONGS_TO',
      fact: 'User belongs to Team Alpha',
      source_node_id: 'User',
      target_node_id: 'Team Alpha',
      valid_from: '2024-01-01T00:00:00Z',
      valid_until: undefined,
    },
    {
      id: '2',
      relationship_type: 'WORKS_ON',
      fact: 'Team Alpha works on Project X',
      source_node_id: 'Team Alpha',
      target_node_id: 'Project X',
      valid_from: '2024-01-15T00:00:00Z',
      valid_until: '2024-06-30T00:00:00Z',
    },
  ];

  const mockTimeline = [
    {
      fact: 'Project X started',
      relationship_type: 'STARTED',
      valid_from: '2024-01-01T00:00:00Z',
      valid_until: null,
      status: 'current' as const,
      created_at: '2024-01-01T00:00:00Z',
      expired_at: null,
    },
    {
      fact: 'Initial milestone reached',
      relationship_type: 'ACHIEVED',
      valid_from: '2024-02-15T00:00:00Z',
      valid_until: '2024-03-01T00:00:00Z',
      status: 'superseded' as const,
      created_at: '2024-02-15T00:00:00Z',
      expired_at: '2024-03-01T00:00:00Z',
    },
  ];

  describe('empty state', () => {
    it('should return null when no relationships or timeline', () => {
      const { container } = renderWithProvider(<KnowledgeGraphView />);
      // Component returns null, so no Card should be rendered (just Mantine style tags)
      expect(container.querySelector('.mantine-Card-root')).toBeNull();
    });

    it('should return null when relationships array is empty', () => {
      const { container } = renderWithProvider(<KnowledgeGraphView relationships={[]} />);
      expect(container.querySelector('.mantine-Card-root')).toBeNull();
    });

    it('should return null when timeline array is empty', () => {
      const { container } = renderWithProvider(<KnowledgeGraphView timeline={[]} />);
      expect(container.querySelector('.mantine-Card-root')).toBeNull();
    });
  });

  describe('relationships view', () => {
    it('should render relationships when provided', () => {
      renderWithProvider(<KnowledgeGraphView relationships={mockRelationships} />);
      expect(screen.getByText('Knowledge Graph Relationships (2)')).toBeDefined();
    });

    it('should display relationship table headers', () => {
      renderWithProvider(<KnowledgeGraphView relationships={mockRelationships} />);
      expect(screen.getByText('Relationship')).toBeDefined();
      expect(screen.getByText('Type')).toBeDefined();
      expect(screen.getByText('Valid')).toBeDefined();
    });

    it('should display source and target nodes', () => {
      renderWithProvider(<KnowledgeGraphView relationships={mockRelationships} />);
      expect(screen.getByText('User')).toBeDefined();
      // "Team Alpha" appears twice - as target in first relationship and source in second
      const teamAlphaElements = screen.getAllByText('Team Alpha');
      expect(teamAlphaElements.length).toBe(2);
      expect(screen.getByText('Project X')).toBeDefined();
    });

    it('should display fact descriptions', () => {
      renderWithProvider(<KnowledgeGraphView relationships={mockRelationships} />);
      expect(screen.getByText('User belongs to Team Alpha')).toBeDefined();
      expect(screen.getByText('Team Alpha works on Project X')).toBeDefined();
    });

    it('should display relationship type badges', () => {
      renderWithProvider(<KnowledgeGraphView relationships={mockRelationships} />);
      expect(screen.getByText('BELONGS_TO')).toBeDefined();
      expect(screen.getByText('WORKS_ON')).toBeDefined();
    });

    it('should prioritize relationships over timeline when both provided', () => {
      renderWithProvider(
        <KnowledgeGraphView relationships={mockRelationships} timeline={mockTimeline} />
      );
      // Should show relationships view, not timeline
      expect(screen.getByText('Knowledge Graph Relationships (2)')).toBeDefined();
      expect(screen.queryByText('Knowledge Evolution Timeline')).toBeNull();
    });
  });

  describe('timeline view', () => {
    it('should render timeline when provided', () => {
      renderWithProvider(<KnowledgeGraphView timeline={mockTimeline} />);
      expect(screen.getByText('Knowledge Evolution Timeline (2 events)')).toBeDefined();
    });

    it('should display fact text for each timeline item', () => {
      renderWithProvider(<KnowledgeGraphView timeline={mockTimeline} />);
      expect(screen.getByText('Project X started')).toBeDefined();
      expect(screen.getByText('Initial milestone reached')).toBeDefined();
    });

    it('should display status badges', () => {
      renderWithProvider(<KnowledgeGraphView timeline={mockTimeline} />);
      expect(screen.getByText('current')).toBeDefined();
      expect(screen.getByText('superseded')).toBeDefined();
    });

    it('should display relationship type badges', () => {
      renderWithProvider(<KnowledgeGraphView timeline={mockTimeline} />);
      expect(screen.getByText('STARTED')).toBeDefined();
      expect(screen.getByText('ACHIEVED')).toBeDefined();
    });

    it('should display valid date ranges', () => {
      renderWithProvider(<KnowledgeGraphView timeline={mockTimeline} />);
      // Dates should be formatted
      const validTexts = screen.getAllByText(/Valid:/);
      expect(validTexts.length).toBe(2);
    });

    it('should display created dates', () => {
      renderWithProvider(<KnowledgeGraphView timeline={mockTimeline} />);
      const createdTexts = screen.getAllByText(/Created:/);
      expect(createdTexts.length).toBe(2);
    });
  });
});
