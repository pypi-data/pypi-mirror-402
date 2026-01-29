/**
 * RightPanel Component Tests
 *
 * Tests the right panel component (currently placeholder).
 */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { RightPanel } from '../../../src/rag/components/layout/RightPanel';

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('RightPanel', () => {
  describe('rendering', () => {
    it('should render without crashing', () => {
      const { container } = renderWithProvider(<RightPanel />);
      expect(container).toBeDefined();
    });

    it('should return null (placeholder component)', () => {
      const { container } = renderWithProvider(<RightPanel />);
      // The component returns null, so container should have no child elements (just style tags from Mantine)
      expect(container.querySelector('.mantine-Card-root')).toBeNull();
    });
  });
});
