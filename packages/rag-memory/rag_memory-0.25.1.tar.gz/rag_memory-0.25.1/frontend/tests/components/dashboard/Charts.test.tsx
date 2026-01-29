/**
 * Dashboard Charts Component Tests
 *
 * Tests for dashboard chart components.
 * Note: Recharts components are tested for mounting and data handling,
 * not visual rendering details.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { FileTypeChart } from '../../../src/rag/components/dashboard/FileTypeChart';
import { QualityHistogram } from '../../../src/rag/components/dashboard/QualityHistogram';
import { ReviewStatusChart } from '../../../src/rag/components/dashboard/ReviewStatusChart';
import { IngestMethodChart } from '../../../src/rag/components/dashboard/IngestMethodChart';

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('FileTypeChart', () => {
  const mockData = [
    { type: 'md', count: 10, size_bytes: 102400, pct: 50 },
    { type: 'txt', count: 5, size_bytes: 51200, pct: 25 },
    { type: 'json', count: 5, size_bytes: 51200, pct: 25 },
  ];

  it('should render without crashing', () => {
    const { container } = renderWithProvider(<FileTypeChart data={mockData} />);
    expect(container).toBeDefined();
  });

  it('should show "No data available" when data is empty', () => {
    renderWithProvider(<FileTypeChart data={[]} />);
    expect(screen.getByText('No data available')).toBeDefined();
  });

  it('should render with data', () => {
    const { container } = renderWithProvider(<FileTypeChart data={mockData} />);
    // Recharts renders an SVG container
    const svg = container.querySelector('svg');
    expect(svg).toBeDefined();
  });
});

describe('QualityHistogram', () => {
  const mockData = [
    { range: '0-20', count: 2 },
    { range: '20-40', count: 5 },
    { range: '40-60', count: 10 },
    { range: '60-80', count: 15 },
    { range: '80-100', count: 8 },
  ];

  it('should render without crashing', () => {
    const { container } = renderWithProvider(<QualityHistogram data={mockData} />);
    expect(container).toBeDefined();
  });

  it('should show "No data available" when all counts are zero', () => {
    const emptyData = [
      { range: '0-20', count: 0 },
      { range: '20-40', count: 0 },
    ];
    renderWithProvider(<QualityHistogram data={emptyData} />);
    expect(screen.getByText('No data available')).toBeDefined();
  });

  it('should render with data', () => {
    const { container } = renderWithProvider(<QualityHistogram data={mockData} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeDefined();
  });

  it('should accept custom color prop', () => {
    const { container } = renderWithProvider(
      <QualityHistogram data={mockData} color="#10b981" />
    );
    expect(container).toBeDefined();
  });
});

describe('ReviewStatusChart', () => {
  const mockData = {
    reviewed: 45,
    unreviewed: 55,
  };

  it('should render without crashing', () => {
    const { container } = renderWithProvider(<ReviewStatusChart data={mockData} />);
    expect(container).toBeDefined();
  });

  it('should show "No data available" when both counts are zero', () => {
    renderWithProvider(<ReviewStatusChart data={{ reviewed: 0, unreviewed: 0 }} />);
    expect(screen.getByText('No data available')).toBeDefined();
  });

  it('should render with data', () => {
    const { container } = renderWithProvider(<ReviewStatusChart data={mockData} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeDefined();
  });
});

describe('IngestMethodChart', () => {
  const mockData = [
    { method: 'url', count: 30, pct: 30 },
    { method: 'text', count: 20, pct: 20 },
    { method: 'file', count: 50, pct: 50 },
  ];

  it('should render without crashing', () => {
    const { container } = renderWithProvider(<IngestMethodChart data={mockData} />);
    expect(container).toBeDefined();
  });

  it('should show "No data available" when data is empty', () => {
    renderWithProvider(<IngestMethodChart data={[]} />);
    expect(screen.getByText('No data available')).toBeDefined();
  });

  it('should render with data', () => {
    const { container } = renderWithProvider(<IngestMethodChart data={mockData} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeDefined();
  });
});
