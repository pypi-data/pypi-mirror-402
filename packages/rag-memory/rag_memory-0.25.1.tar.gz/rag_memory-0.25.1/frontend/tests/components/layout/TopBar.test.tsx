/**
 * TopBar Component Tests
 *
 * Tests the header component with Lumentor branding.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { TopBar } from '../../../src/rag/components/layout/TopBar';

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('TopBar', () => {
  describe('rendering', () => {
    it('should render without crashing', () => {
      const { container } = renderWithProvider(<TopBar />);
      expect(container).toBeDefined();
    });

    it('should display Lumentor branding', () => {
      renderWithProvider(<TopBar />);
      expect(screen.getByText('Lumentor')).toBeDefined();
    });

    it('should display tagline', () => {
      renderWithProvider(<TopBar />);
      expect(screen.getByText('Knowledge Illuminated')).toBeDefined();
    });

    it('should display logo symbol', () => {
      renderWithProvider(<TopBar />);
      expect(screen.getByText('✦')).toBeDefined();
    });

    it('should have settings button', () => {
      renderWithProvider(<TopBar />);
      const settingsButton = screen.getByRole('button');
      expect(settingsButton).toBeDefined();
    });
  });
});
