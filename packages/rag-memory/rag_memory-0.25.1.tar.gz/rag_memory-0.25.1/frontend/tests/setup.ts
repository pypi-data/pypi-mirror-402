import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll, afterAll } from 'vitest';
import { server } from './mocks/server';

// Establish API mocking before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));

// Reset any request handlers that are declared as a part of tests
afterEach(() => {
  cleanup();
  server.resetHandlers();
});

// Clean up after the tests are finished
afterAll(() => server.close());

// Mock window.matchMedia for Mantine components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Mock ResizeObserver for Mantine and vis-network
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.ResizeObserver = ResizeObserverMock;

// Mock IntersectionObserver
class IntersectionObserverMock {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.IntersectionObserver = IntersectionObserverMock as unknown as typeof IntersectionObserver;

// Mock scrollIntoView - jsdom doesn't implement this
Element.prototype.scrollIntoView = function() {};

// Mock scrollTo - jsdom doesn't implement this either
window.scrollTo = function() {};
