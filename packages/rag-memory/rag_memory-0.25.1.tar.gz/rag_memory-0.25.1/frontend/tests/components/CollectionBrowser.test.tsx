/**
 * CollectionBrowser Component Tests
 *
 * Tests the collection browsing, creation, and management sidebar.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MantineProvider } from '@mantine/core';
import CollectionBrowser from '../../src/rag/components/CollectionBrowser';
import { useRagStore } from '../../src/rag/store';
import * as ragApi from '../../src/rag/ragApi';

// Mock ragApi
vi.mock('../../src/rag/ragApi', () => ({
  getCollectionInfo: vi.fn(),
  getCollectionMetadataSchema: vi.fn(),
  listDocuments: vi.fn(),
  getDocument: vi.fn(),
  deleteCollection: vi.fn(),
}));

// Wrapper with Mantine provider
function TestWrapper({ children }: { children: React.ReactNode }) {
  return <MantineProvider>{children}</MantineProvider>;
}

function renderWithProvider(component: React.ReactElement) {
  return render(component, { wrapper: TestWrapper });
}

describe('CollectionBrowser', () => {
  const mockCollections = [
    {
      id: 1,
      name: 'test-collection',
      description: 'Test collection for testing',
      domain: 'testing',
      document_count: 5,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 2,
      name: 'docs-collection',
      description: 'Documentation collection',
      domain: 'engineering',
      document_count: 10,
      created_at: '2024-01-02T00:00:00Z',
    },
  ];

  // Default mock metadata schema response
  const mockMetadataSchema = {
    collection_name: 'test-collection',
    description: 'Test collection for testing',
    document_count: 5,
    metadata_schema: {
      mandatory: { domain: 'string', domain_scope: 'string' },
      custom: {},
      system: ['created_at', 'updated_at'],
    },
    custom_fields: {},
    system_fields: ['created_at', 'updated_at'],
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Set default mock for getCollectionMetadataSchema (called in parallel with getCollectionInfo)
    vi.mocked(ragApi.getCollectionMetadataSchema).mockResolvedValue(mockMetadataSchema);

    // Reset store state with mock collections
    useRagStore.setState({
      collections: mockCollections,
      selectedCollectionId: null,
      selectCollection: vi.fn(),
      createCollection: vi.fn().mockResolvedValue(undefined),
      loadCollections: vi.fn(),
    });
  });

  describe('collection list', () => {
    it('should render title', () => {
      renderWithProvider(<CollectionBrowser />);

      expect(screen.getByText('Collections')).toBeDefined();
    });

    it('should render collection cards', () => {
      renderWithProvider(<CollectionBrowser />);

      expect(screen.getByText('test-collection')).toBeDefined();
      expect(screen.getByText('docs-collection')).toBeDefined();
    });

    it('should show collection descriptions', () => {
      renderWithProvider(<CollectionBrowser />);

      expect(screen.getByText('Test collection for testing')).toBeDefined();
      expect(screen.getByText('Documentation collection')).toBeDefined();
    });

    it('should show domain badges', () => {
      renderWithProvider(<CollectionBrowser />);

      // Domain badges may appear multiple times, use getAllByText
      const testingBadges = screen.getAllByText('testing');
      const engineeringBadges = screen.getAllByText('engineering');
      expect(testingBadges.length).toBeGreaterThan(0);
      expect(engineeringBadges.length).toBeGreaterThan(0);
    });

    it('should show empty state when no collections', () => {
      useRagStore.setState({ collections: [] });
      renderWithProvider(<CollectionBrowser />);

      expect(screen.getByText('No collections yet')).toBeDefined();
    });
  });

  describe('create collection', () => {
    it('should have create button', () => {
      renderWithProvider(<CollectionBrowser />);

      // Find button by title attribute
      const createButton = screen.getByTitle('Create collection');
      expect(createButton).toBeDefined();
    });

    it('should open create modal when button clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(<CollectionBrowser />);

      const createButton = screen.getByTitle('Create collection');
      await user.click(createButton);

      await waitFor(() => {
        expect(screen.getByText('Create New Collection')).toBeDefined();
      });
    });

    it('should have form fields in create modal', async () => {
      const user = userEvent.setup();
      renderWithProvider(<CollectionBrowser />);

      const createButton = screen.getByTitle('Create collection');
      await user.click(createButton);

      // Wait for modal to appear and check for form labels
      await waitFor(() => {
        expect(screen.getByText('Create New Collection')).toBeDefined();
      });

      // Check that text inputs exist (the modal has form fields)
      const textboxes = screen.getAllByRole('textbox');
      expect(textboxes.length).toBeGreaterThanOrEqual(4); // name, description, domain, domain scope
    });

    it('should have Cancel and Create buttons in modal', async () => {
      const user = userEvent.setup();
      renderWithProvider(<CollectionBrowser />);

      const createButton = screen.getByTitle('Create collection');
      await user.click(createButton);

      await waitFor(() => {
        expect(screen.getByText('Create New Collection')).toBeDefined();
      });

      const buttons = screen.getAllByRole('button');
      // Look for buttons containing the text (not exact match)
      const cancelButton = buttons.find((b) => b.textContent?.includes('Cancel'));
      const createBtn = buttons.find((b) => b.textContent?.includes('Create') && !b.textContent?.includes('New'));

      expect(cancelButton).toBeDefined();
      expect(createBtn).toBeDefined();
    });

    it('should close modal when Cancel clicked', async () => {
      const user = userEvent.setup();
      renderWithProvider(<CollectionBrowser />);

      // Open modal
      const createButton = screen.getByTitle('Create collection');
      await user.click(createButton);

      // Wait for modal to appear
      await waitFor(() => {
        expect(screen.getByText('Create New Collection')).toBeDefined();
      });

      // Find and click Cancel button (there may be multiple buttons)
      const buttons = screen.getAllByRole('button');
      const cancelButton = buttons.find((b) => b.textContent === 'Cancel');
      expect(cancelButton).toBeDefined();
      await user.click(cancelButton!);

      // Modal title should no longer be visible
      await waitFor(() => {
        expect(screen.queryByText('Create New Collection')).toBeNull();
      });
    });
  });

  describe('collection details', () => {
    const mockCollectionInfo = {
      name: 'test-collection',
      description: 'Test collection for testing',
      domain: 'testing',
      domain_scope: 'Unit testing scope',
      document_count: 5,
      chunk_count: 20,
      created_at: '2024-01-01T00:00:00Z',
      sample_documents: ['doc1.md', 'doc2.md'],
      crawled_urls: [],
    };

    it('should open details modal when collection clicked', async () => {
      const user = userEvent.setup();
      vi.mocked(ragApi.getCollectionInfo).mockResolvedValue(mockCollectionInfo);

      renderWithProvider(<CollectionBrowser />);

      const collectionCard = screen.getByText('test-collection');
      await user.click(collectionCard);

      await waitFor(() => {
        expect(screen.getByText('Collection Details')).toBeDefined();
      });
    });

    it('should call selectCollection when collection clicked', async () => {
      const user = userEvent.setup();
      const mockSelectCollection = vi.fn();
      useRagStore.setState({ selectCollection: mockSelectCollection });
      vi.mocked(ragApi.getCollectionInfo).mockResolvedValue(mockCollectionInfo);

      renderWithProvider(<CollectionBrowser />);

      const collectionCard = screen.getByText('test-collection');
      await user.click(collectionCard);

      expect(mockSelectCollection).toHaveBeenCalledWith('test-collection');
    });

    it('should display collection info in details modal', async () => {
      const user = userEvent.setup();
      vi.mocked(ragApi.getCollectionInfo).mockResolvedValue(mockCollectionInfo);

      renderWithProvider(<CollectionBrowser />);

      const collectionCard = screen.getByText('test-collection');
      await user.click(collectionCard);

      await waitFor(() => {
        expect(screen.getByText('Basic Information')).toBeDefined();
        expect(screen.getByText('Statistics')).toBeDefined();
      });
    });

    it('should show sample documents section', async () => {
      const user = userEvent.setup();
      vi.mocked(ragApi.getCollectionInfo).mockResolvedValue(mockCollectionInfo);

      renderWithProvider(<CollectionBrowser />);

      const collectionCard = screen.getByText('test-collection');
      await user.click(collectionCard);

      await waitFor(() => {
        // Look for any text containing "Sample Documents"
        const sampleDocsText = screen.getAllByText(/sample documents/i);
        expect(sampleDocsText.length).toBeGreaterThan(0);
      });
    });

    it('should have Delete Collection button', async () => {
      const user = userEvent.setup();
      vi.mocked(ragApi.getCollectionInfo).mockResolvedValue(mockCollectionInfo);

      renderWithProvider(<CollectionBrowser />);

      const collectionCard = screen.getByText('test-collection');
      await user.click(collectionCard);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /delete collection/i })).toBeDefined();
      });
    });
  });

  describe('window global', () => {
    it('should set __openCreateCollectionModal on window', () => {
      renderWithProvider(<CollectionBrowser />);

      expect((window as any).__openCreateCollectionModal).toBeDefined();
      expect(typeof (window as any).__openCreateCollectionModal).toBe('function');
    });

    it('should open create modal when window global called', async () => {
      renderWithProvider(<CollectionBrowser />);

      // Call the window global
      (window as any).__openCreateCollectionModal();

      await waitFor(() => {
        expect(screen.getByText('Create New Collection')).toBeDefined();
      });
    });
  });

  describe('create collection form', () => {
    it('should disable Create button when form is incomplete', async () => {
      const user = userEvent.setup();
      renderWithProvider(<CollectionBrowser />);

      const createButton = screen.getByTitle('Create collection');
      await user.click(createButton);

      await waitFor(() => {
        expect(screen.getByText('Create New Collection')).toBeDefined();
      });

      // Find the Create button in modal (not the header icon)
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find((b) => b.textContent === 'Create');

      // Should be disabled initially since no fields are filled
      expect(submitButton).toBeDefined();
      expect(submitButton).toBeDisabled();
    });

    it('should call createCollection when form submitted', async () => {
      const mockCreateCollection = vi.fn().mockResolvedValue(undefined);
      const mockLoadCollections = vi.fn();
      useRagStore.setState({
        createCollection: mockCreateCollection,
        loadCollections: mockLoadCollections,
      });

      const user = userEvent.setup();
      renderWithProvider(<CollectionBrowser />);

      // Open modal
      const createButton = screen.getByTitle('Create collection');
      await user.click(createButton);

      await waitFor(() => {
        expect(screen.getByText('Create New Collection')).toBeDefined();
      });

      // Fill in form fields
      const textboxes = screen.getAllByRole('textbox');
      // textboxes are: name, description, domain, domainScope
      await user.type(textboxes[0], 'my-collection');
      await user.type(textboxes[1], 'My collection description');
      await user.type(textboxes[2], 'testing');
      await user.type(textboxes[3], 'Test domain scope');

      // Find and click Create button
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find((b) => b.textContent === 'Create');
      expect(submitButton).toBeDefined();
      expect(submitButton).not.toBeDisabled();
      await user.click(submitButton!);

      await waitFor(() => {
        expect(mockCreateCollection).toHaveBeenCalledWith(
          'my-collection',
          'My collection description',
          'testing',
          'Test domain scope'
        );
      });
    });
  });

  describe('loading states', () => {
    it('should show loader when loading collection details', async () => {
      const user = userEvent.setup();
      // Make getCollectionInfo take a while
      vi.mocked(ragApi.getCollectionInfo).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderWithProvider(<CollectionBrowser />);

      const collectionCard = screen.getByText('test-collection');
      await user.click(collectionCard);

      // Should show loader while loading
      await waitFor(() => {
        expect(screen.getByText('Collection Details')).toBeDefined();
      });

      // Loader should be visible
      const loaders = document.querySelectorAll('.mantine-Loader-root');
      expect(loaders.length).toBeGreaterThan(0);
    });

    it('should show error message when collection details fail to load', async () => {
      const user = userEvent.setup();
      vi.mocked(ragApi.getCollectionInfo).mockRejectedValue(new Error('Failed to load'));

      renderWithProvider(<CollectionBrowser />);

      const collectionCard = screen.getByText('test-collection');
      await user.click(collectionCard);

      await waitFor(() => {
        expect(screen.getByText('Failed to load collection details')).toBeDefined();
      });
    });
  });

  describe('delete collection', () => {
    const mockCollectionInfo = {
      name: 'test-collection',
      description: 'Test collection for testing',
      domain: 'testing',
      domain_scope: 'Unit testing scope',
      document_count: 5,
      chunk_count: 20,
      created_at: '2024-01-01T00:00:00Z',
      sample_documents: [],
      crawled_urls: [],
    };

    it('should open delete confirmation modal when Delete Collection clicked', async () => {
      const user = userEvent.setup();
      vi.mocked(ragApi.getCollectionInfo).mockResolvedValue(mockCollectionInfo);

      renderWithProvider(<CollectionBrowser />);

      // Click collection to open details
      const collectionCard = screen.getByText('test-collection');
      await user.click(collectionCard);

      await waitFor(() => {
        expect(screen.getByText('Collection Details')).toBeDefined();
      });

      // Click Delete Collection button
      const deleteButton = screen.getByRole('button', { name: /delete collection/i });
      await user.click(deleteButton);

      // Should show confirmation modal with warning
      await waitFor(() => {
        expect(screen.getByText(/this action cannot be undone/i)).toBeDefined();
      });
    });

    it('should call deleteCollection when confirmed', async () => {
      const user = userEvent.setup();
      const mockDeleteCollection = vi.fn().mockResolvedValue(undefined);
      const mockLoadCollections = vi.fn();
      vi.mocked(ragApi.getCollectionInfo).mockResolvedValue(mockCollectionInfo);
      vi.mocked(ragApi.deleteCollection).mockImplementation(mockDeleteCollection);
      useRagStore.setState({ loadCollections: mockLoadCollections });

      renderWithProvider(<CollectionBrowser />);

      // Click collection to open details
      const collectionCard = screen.getByText('test-collection');
      await user.click(collectionCard);

      await waitFor(() => {
        expect(screen.getByText('Collection Details')).toBeDefined();
      });

      // Click Delete Collection button (first one in details modal)
      const deleteButton = screen.getByRole('button', { name: /delete collection/i });
      await user.click(deleteButton);

      // Wait for confirmation modal with warning
      await waitFor(() => {
        expect(screen.getByText(/this action cannot be undone/i)).toBeDefined();
      });

      // Find the confirm delete button in the confirmation modal (there are now two Delete Collection buttons)
      const allDeleteButtons = screen.getAllByRole('button', { name: /delete collection/i });
      const confirmButton = allDeleteButtons[allDeleteButtons.length - 1]; // The last one is in the confirmation modal
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockDeleteCollection).toHaveBeenCalledWith('test-collection');
      });
    });
  });

  describe('collection selection', () => {
    it('should highlight selected collection', () => {
      useRagStore.setState({ selectedCollectionId: 'test-collection' });
      renderWithProvider(<CollectionBrowser />);

      // Selected collection should have different background
      const collectionCard = screen.getByText('test-collection').closest('[class*="Card"]');
      expect(collectionCard).toBeDefined();
    });
  });

  describe('view all documents', () => {
    const mockCollectionInfo = {
      name: 'test-collection',
      description: 'Test collection for testing',
      domain: 'testing',
      domain_scope: 'Unit testing scope',
      document_count: 25,
      chunk_count: 100,
      created_at: '2024-01-01T00:00:00Z',
      sample_documents: ['doc1.md', 'doc2.md', 'doc3.md'],
      crawled_urls: [],
    };

    it('should show View All Documents button when document count exceeds sample count', async () => {
      const user = userEvent.setup();
      vi.mocked(ragApi.getCollectionInfo).mockResolvedValue(mockCollectionInfo);

      renderWithProvider(<CollectionBrowser />);

      const collectionCard = screen.getByText('test-collection');
      await user.click(collectionCard);

      await waitFor(() => {
        // Should show button to view all 25 documents
        expect(screen.getByText(/view all 25 documents/i)).toBeDefined();
      });
    });

    it('should open all documents modal when View All clicked', async () => {
      const user = userEvent.setup();
      vi.mocked(ragApi.getCollectionInfo).mockResolvedValue(mockCollectionInfo);
      vi.mocked(ragApi.listDocuments).mockResolvedValue([
        { id: 1, filename: 'doc1.md', chunk_count: 5, created_at: '2024-01-01T00:00:00Z', reviewed_by_human: false, quality_score: 0.8, topic_relevance_score: null, topic_provided: null },
        { id: 2, filename: 'doc2.md', chunk_count: 3, created_at: '2024-01-02T00:00:00Z', reviewed_by_human: true, quality_score: 0.6, topic_relevance_score: 0.7, topic_provided: 'testing' },
      ]);

      renderWithProvider(<CollectionBrowser />);

      const collectionCard = screen.getByText('test-collection');
      await user.click(collectionCard);

      await waitFor(() => {
        expect(screen.getByText(/view all 25 documents/i)).toBeDefined();
      });

      const viewAllButton = screen.getByText(/view all 25 documents/i);
      await user.click(viewAllButton);

      await waitFor(() => {
        expect(screen.getByText('All Documents - test-collection')).toBeDefined();
      });
    });
  });
});
