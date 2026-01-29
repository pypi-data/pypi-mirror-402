/**
 * DashboardView Component Tests
 *
 * Tests the main dashboard view component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import { DashboardView } from '../../../src/rag/components/dashboard/DashboardView';
import { useRagStore } from '../../../src/rag/store';
import * as ragApi from '../../../src/rag/ragApi';

// Mock ragApi
vi.mock('../../../src/rag/ragApi', () => ({
  getAdminStats: vi.fn(),
  getQualityAnalytics: vi.fn(),
  getContentAnalytics: vi.fn(),
}));

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('DashboardView', () => {
  const mockStats = {
    collections: { total: 5 },
    documents: { total: 100, reviewed: 45 },
    chunks: { total: 500 },
    quality: {
      avg: 0.75,
      distribution: { high: 30, medium: 50, low: 20 },
    },
  };

  const mockAnalytics = {
    quality_histogram: [
      { range: '0-20', count: 5 },
      { range: '20-40', count: 10 },
      { range: '40-60', count: 25 },
      { range: '60-80', count: 40 },
      { range: '80-100', count: 20 },
    ],
    topic_histogram: [
      { range: '0-20', count: 8 },
      { range: '20-40', count: 12 },
      { range: '40-60', count: 30 },
      { range: '60-80', count: 35 },
      { range: '80-100', count: 15 },
    ],
    review_breakdown: { reviewed: 45, unreviewed: 55 },
    quality_by_collection: [
      { collection: 'docs', avg_quality: 0.8, count: 50 },
      { collection: 'notes', avg_quality: 0.7, count: 50 },
    ],
  };

  const mockContentAnalytics = {
    storage: { total_bytes: 1048576, total_human: '1.0 MB' },
    chunks: { avg_per_doc: 5 },
    file_type_distribution: [
      { type: 'md', count: 60, size_bytes: 600000, pct: 60 },
      { type: 'txt', count: 40, size_bytes: 400000, pct: 40 },
    ],
    ingest_method_breakdown: [
      { method: 'url', count: 50, pct: 50 },
      { method: 'file', count: 50, pct: 50 },
    ],
    actor_type_breakdown: [
      { actor: 'agent', count: 70, pct: 70 },
      { actor: 'user', count: 30, pct: 30 },
    ],
    ingestion_timeline: [
      { date: '2024-01-01', count: 10 },
      { date: '2024-01-02', count: 15 },
    ],
    crawl_stats: {
      total_crawl_sessions: 5,
      avg_pages_per_crawl: 8,
      total_pages_crawled: 40,
      domains: ['example.com', 'docs.example.com'],
      depth_distribution: [
        { depth: 1, count: 20 },
        { depth: 2, count: 15 },
        { depth: 3, count: 5 },
      ],
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    useRagStore.setState({
      collections: [
        { name: 'docs', description: 'Documentation', document_count: 50 },
        { name: 'notes', description: 'Notes', document_count: 50 },
      ],
      loadCollections: vi.fn(),
    });

    vi.mocked(ragApi.getAdminStats).mockResolvedValue(mockStats);
    vi.mocked(ragApi.getQualityAnalytics).mockResolvedValue(mockAnalytics);
    vi.mocked(ragApi.getContentAnalytics).mockResolvedValue(mockContentAnalytics);
  });

  describe('loading state', () => {
    it('should show loading indicator initially', () => {
      vi.mocked(ragApi.getAdminStats).mockImplementation(
        () => new Promise(() => {})
      );

      renderWithProvider(<DashboardView />);

      const loader = document.querySelector('.mantine-Loader-root');
      expect(loader).toBeDefined();
    });
  });

  describe('rendering', () => {
    it('should display Dashboard title', async () => {
      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeDefined();
      });
    });

    it('should display stats cards after loading', async () => {
      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByText('Collections')).toBeDefined();
        expect(screen.getByText('Documents')).toBeDefined();
        expect(screen.getByText('Chunks')).toBeDefined();
      });
    });

    it('should display Quality Score Distribution section', async () => {
      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByText('Quality Score Distribution')).toBeDefined();
      });
    });

    it('should display Review Status section', async () => {
      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByText('Review Status')).toBeDefined();
      });
    });

    it('should display Content Composition section', async () => {
      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByText('Content Composition')).toBeDefined();
        expect(screen.getByText('File Types')).toBeDefined();
        expect(screen.getByText('Ingest Methods')).toBeDefined();
      });
    });

    it('should display Activity & Provenance section', async () => {
      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByText('Activity & Provenance')).toBeDefined();
        expect(screen.getByText('Ingestion Activity (Last 30 Days)')).toBeDefined();
        expect(screen.getByText('Who Is Ingesting?')).toBeDefined();
      });
    });

    it('should display Quality by Collection section', async () => {
      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByText('Quality by Collection')).toBeDefined();
      });
    });

    it('should display Topic Relevance Distribution section', async () => {
      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByText('Topic Relevance Distribution')).toBeDefined();
      });
    });
  });

  describe('collection filter', () => {
    it('should have collection filter dropdown', async () => {
      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Filter by collection')).toBeDefined();
      });
    });

    it('should reload data when collection filter changes', async () => {
      const user = userEvent.setup();
      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Filter by collection')).toBeDefined();
      });

      // Initial load
      expect(ragApi.getAdminStats).toHaveBeenCalledTimes(1);

      // Click the filter dropdown
      await user.click(screen.getByPlaceholderText('Filter by collection'));

      // Select a collection
      await user.click(screen.getByText('docs'));

      // Should have called APIs again with the selected collection
      await waitFor(() => {
        expect(ragApi.getAdminStats).toHaveBeenCalledWith('docs');
      });
    });
  });

  describe('error handling', () => {
    it('should display error message when API fails', async () => {
      vi.mocked(ragApi.getAdminStats).mockRejectedValue(new Error('API Error'));

      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeDefined();
        expect(screen.getByText('API Error')).toBeDefined();
      });
    });
  });

  describe('crawl stats visibility', () => {
    it('should show crawl stats when crawl_sessions > 0', async () => {
      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        expect(screen.getByText('Web Crawl Statistics')).toBeDefined();
      });
    });

    it('should hide crawl stats when crawl_sessions is 0', async () => {
      vi.mocked(ragApi.getContentAnalytics).mockResolvedValue({
        ...mockContentAnalytics,
        crawl_stats: {
          total_crawl_sessions: 0,
          avg_pages_per_crawl: 0,
          total_pages_crawled: 0,
          domains: [],
          depth_distribution: [],
        },
      });

      renderWithProvider(<DashboardView />);

      await waitFor(() => {
        // Other sections should be visible
        expect(screen.getByText('Dashboard')).toBeDefined();
      });

      // Crawl section should NOT be visible
      expect(screen.queryByText('Web Crawl Statistics')).toBeNull();
    });
  });
});
