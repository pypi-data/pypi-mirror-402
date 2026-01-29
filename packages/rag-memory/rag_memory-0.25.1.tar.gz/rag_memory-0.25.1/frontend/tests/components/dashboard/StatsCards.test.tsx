/**
 * StatsCards Component Tests
 *
 * Tests the dashboard statistics cards display.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { StatsCards } from '../../../src/rag/components/dashboard/StatsCards';
import type { AdminStats, ContentAnalytics } from '../../../src/rag/ragApi';

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('StatsCards', () => {
  const baseStats: AdminStats = {
    collections: { total: 5 },
    documents: { total: 150, reviewed: 45 },
    chunks: { total: 1250 },
    quality: {
      avg: 0.78,
      distribution: { high: 30, medium: 85, low: 35 },
    },
  };

  const contentAnalytics: ContentAnalytics = {
    storage: {
      total_bytes: 1048576,
      total_human: '1.0 MB',
    },
    chunks: {
      avg_per_doc: 8.3,
    },
    file_types: [],
    collection_types: [],
    ingestion_methods: [],
  };

  describe('rendering', () => {
    it('should render all four stat cards', () => {
      renderWithProvider(<StatsCards stats={baseStats} />);

      expect(screen.getByText('Collections')).toBeDefined();
      expect(screen.getByText('Documents')).toBeDefined();
      expect(screen.getByText('Chunks')).toBeDefined();
      expect(screen.getByText('Avg Quality')).toBeDefined();
    });

    it('should display collection count', () => {
      renderWithProvider(<StatsCards stats={baseStats} />);

      expect(screen.getByText('5')).toBeDefined();
    });

    it('should display document count with reviewed count', () => {
      renderWithProvider(<StatsCards stats={baseStats} />);

      expect(screen.getByText('150')).toBeDefined();
      expect(screen.getByText('45 reviewed')).toBeDefined();
    });

    it('should display chunk count', () => {
      renderWithProvider(<StatsCards stats={baseStats} />);

      expect(screen.getByText('1,250')).toBeDefined(); // Formatted with commas
    });

    it('should display quality percentage', () => {
      renderWithProvider(<StatsCards stats={baseStats} />);

      expect(screen.getByText('78%')).toBeDefined();
      expect(screen.getByText('30 high, 85 med, 35 low')).toBeDefined();
    });
  });

  describe('quality edge cases', () => {
    it('should display N/A when avg quality is null', () => {
      const statsWithNullQuality: AdminStats = {
        ...baseStats,
        quality: {
          avg: null,
          distribution: { high: 0, medium: 0, low: 0 },
        },
      };

      renderWithProvider(<StatsCards stats={statsWithNullQuality} />);

      expect(screen.getByText('N/A')).toBeDefined();
    });

    it('should not show quality distribution when all zeros', () => {
      const statsWithZeroDistribution: AdminStats = {
        ...baseStats,
        quality: {
          avg: 0.5,
          distribution: { high: 0, medium: 0, low: 0 },
        },
      };

      renderWithProvider(<StatsCards stats={statsWithZeroDistribution} />);

      expect(screen.queryByText(/high, .* med, .* low/)).toBeNull();
    });
  });

  describe('content analytics', () => {
    it('should show storage size when content analytics provided', () => {
      renderWithProvider(
        <StatsCards stats={baseStats} contentAnalytics={contentAnalytics} />
      );

      expect(screen.getByText(/45 reviewed.*1.0 MB/)).toBeDefined();
    });

    it('should show avg chunks per doc when content analytics provided', () => {
      renderWithProvider(
        <StatsCards stats={baseStats} contentAnalytics={contentAnalytics} />
      );

      expect(screen.getByText('~8.3 avg per doc')).toBeDefined();
    });

    it('should handle null content analytics gracefully', () => {
      renderWithProvider(
        <StatsCards stats={baseStats} contentAnalytics={null} />
      );

      // Should render without crashing
      expect(screen.getByText('Collections')).toBeDefined();
      expect(screen.queryByText(/avg per doc/)).toBeNull();
    });
  });

  describe('large numbers', () => {
    it('should format large numbers with commas', () => {
      const largeStats: AdminStats = {
        ...baseStats,
        documents: { total: 12500, reviewed: 5000 },
        chunks: { total: 125000 },
      };

      renderWithProvider(<StatsCards stats={largeStats} />);

      expect(screen.getByText('12,500')).toBeDefined();
      expect(screen.getByText('125,000')).toBeDefined();
    });
  });
});
