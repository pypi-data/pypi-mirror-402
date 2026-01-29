/**
 * DocumentsView - Grid view of all documents with filters
 *
 * Features:
 * - Document grid with amber accent borders
 * - Filter by collection, review status, quality, topic relevance
 * - Search by title
 * - Sort options
 * - Click to view full document
 * - "Add Documents" button
 */

import { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Title,
  Select,
  MultiSelect,
  Button,
  Card,
  Text,
  Group,
  Badge,
  Loader,
  Grid,
  Stack,
  ActionIcon,
  Tooltip,
  TextInput,
  SegmentedControl,
  Paper,
} from '@mantine/core';
import { IconPlus, IconFileText, IconTrash, IconSearch, IconCheck, IconRefresh } from '@tabler/icons-react';
import { useRagStore } from '../../store';
import * as ragApi from '../../ragApi';
import type { DocumentListItemDetailed, Document } from '../../types';
import { IngestionModal } from '../modals/IngestionModal';
import { ConfirmDeleteModal, DeleteTarget } from '../modals/ConfirmDeleteModal';
import DocumentModal from '../DocumentModal';

export function DocumentsView() {
  const { collections } = useRagStore();
  const [selectedCollections, setSelectedCollections] = useState<string[]>([]);
  const [collectionFilterMode, setCollectionFilterMode] = useState<string>('include');
  const [documents, setDocuments] = useState<DocumentListItemDetailed[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [reviewFilter, setReviewFilter] = useState<string>('all');
  const [qualityFilter, setQualityFilter] = useState<string>('all');
  const [topicFilter, setTopicFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('date_desc');

  // Document viewer modal state
  const [isDocViewerOpen, setIsDocViewerOpen] = useState(false);
  const [viewingDocument, setViewingDocument] = useState<Document | null>(null);

  // Ingestion modal state
  const [isIngestionModalOpen, setIsIngestionModalOpen] = useState(false);

  // Delete confirmation state
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Load all documents on mount (collection filtering is done client-side)
  useEffect(() => {
    loadDocuments();
  }, []);

  // Auto-refresh polling: Fetch documents every 10 seconds to reflect external changes
  // (e.g., documents added via MCP tools, CLI, or other clients)
  useEffect(() => {
    const POLLING_INTERVAL = 10000; // 10 seconds

    const poll = async () => {
      // Only poll if the document is visible (save resources when tab is hidden)
      if (!document.hidden) {
        try {
          // Always fetch all documents - collection filtering is client-side
          const docs = await ragApi.listDocuments(undefined, 1000, 0, true);
          setDocuments(docs);
        } catch (error) {
          console.error('[Polling] Failed to refresh documents:', error);
        }
      }
    };

    // Set up interval
    const intervalId = setInterval(poll, POLLING_INTERVAL);

    // Also poll when tab becomes visible again
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        poll();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Cleanup on unmount
    return () => {
      clearInterval(intervalId);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      // Fetch all documents - collection filtering is done client-side for multi-select support
      const docs = await ragApi.listDocuments(undefined, 1000, 0, true);
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Manual refresh handler
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const docs = await ragApi.listDocuments(undefined, 1000, 0, true);
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to refresh documents:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Filter and sort documents
  const filteredDocuments = useMemo(() => {
    let filtered = [...documents];

    // Collection filter (multi-select with include/exclude mode)
    if (selectedCollections.length > 0) {
      if (collectionFilterMode === 'include') {
        // Include: only show documents from selected collections
        filtered = filtered.filter((doc) =>
          doc.collections?.some((c) => selectedCollections.includes(c)) ?? false
        );
      } else {
        // Exclude: show all documents EXCEPT those from selected collections
        // Documents with no collections are kept (not excluded)
        filtered = filtered.filter((doc) =>
          !doc.collections?.length || !doc.collections.some((c) => selectedCollections.includes(c))
        );
      }
    }

    // Search filter (filename)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((doc) =>
        doc.filename.toLowerCase().includes(query)
      );
    }

    // Review status filter
    if (reviewFilter === 'reviewed') {
      filtered = filtered.filter((doc) => doc.reviewed_by_human === true);
    } else if (reviewFilter === 'not_reviewed') {
      filtered = filtered.filter((doc) => doc.reviewed_by_human === false);
    }

    // Quality score filter
    if (qualityFilter === 'high') {
      filtered = filtered.filter((doc) => doc.quality_score !== null && doc.quality_score >= 0.7);
    } else if (qualityFilter === 'medium') {
      filtered = filtered.filter((doc) => doc.quality_score !== null && doc.quality_score >= 0.4 && doc.quality_score < 0.7);
    } else if (qualityFilter === 'low') {
      filtered = filtered.filter((doc) => doc.quality_score !== null && doc.quality_score < 0.4);
    }

    // Topic relevance filter
    if (topicFilter === 'high') {
      filtered = filtered.filter((doc) => doc.topic_relevance_score !== null && doc.topic_relevance_score >= 0.7);
    } else if (topicFilter === 'medium') {
      filtered = filtered.filter((doc) => doc.topic_relevance_score !== null && doc.topic_relevance_score >= 0.4 && doc.topic_relevance_score < 0.7);
    } else if (topicFilter === 'low') {
      filtered = filtered.filter((doc) => doc.topic_relevance_score !== null && doc.topic_relevance_score < 0.4);
    } else if (topicFilter === 'none') {
      filtered = filtered.filter((doc) => doc.topic_relevance_score === null);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'date_desc':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'date_asc':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'name_asc':
          return a.filename.localeCompare(b.filename);
        case 'name_desc':
          return b.filename.localeCompare(a.filename);
        case 'quality_desc':
          return (b.quality_score ?? 0) - (a.quality_score ?? 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [documents, selectedCollections, collectionFilterMode, searchQuery, reviewFilter, qualityFilter, topicFilter, sortBy]);

  const handleViewDocument = async (documentId: number) => {
    setIsDocViewerOpen(true);
    setViewingDocument(null);

    try {
      const doc = await ragApi.getDocument(documentId);
      setViewingDocument(doc);
    } catch (error) {
      console.error('Failed to load document:', error);
      setViewingDocument(null);
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, doc: DocumentListItemDetailed) => {
    e.stopPropagation(); // Prevent card click
    setDeleteTarget({
      type: 'document',
      name: doc.filename,
    });
    setIsDeleteModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    setIsDeleting(true);
    try {
      // Find the document ID by filename
      const docToDelete = documents.find(d => d.filename === deleteTarget.name);
      if (docToDelete) {
        await ragApi.deleteDocument(docToDelete.id);
        // Reload documents after deletion
        await loadDocuments();
      }
      setIsDeleteModalOpen(false);
      setDeleteTarget(null);
    } catch (error) {
      console.error('Failed to delete document:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  // Collection options for MultiSelect (no "All Collections" - empty selection = all)
  const collectionOptions = (collections || [])
    .filter(c => c && c.name)
    .map(c => ({ label: c.name, value: c.name }));

  return (
    <>
      <Box style={{ animation: 'fadeIn 0.4s ease' }}>
        {/* Header */}
        <Group justify="space-between" mb={24}>
          <Group gap="sm">
            <Title
              order={2}
              style={{
                fontFamily: 'Playfair Display, Georgia, serif',
                fontWeight: 700,
                background: 'linear-gradient(135deg, var(--amber-light), var(--amber))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}
            >
              Documents
            </Title>
            <Tooltip label="Refresh documents">
              <ActionIcon
                variant="subtle"
                color="gray"
                onClick={handleRefresh}
                loading={isRefreshing}
                size="lg"
              >
                <IconRefresh size={20} />
              </ActionIcon>
            </Tooltip>
          </Group>

          <Button
            leftSection={<IconPlus size={18} />}
            variant="filled"
            color="amber"
            onClick={() => setIsIngestionModalOpen(true)}
            style={{
              background: 'linear-gradient(135deg, var(--amber) 0%, var(--amber-dark) 100%)',
            }}
          >
            Add Documents
          </Button>
        </Group>

        {/* Filters */}
        <Paper p="md" mb={24} withBorder style={{ background: 'var(--charcoal-light)' }}>
          <Stack gap="md">
            {/* Row 1: Search, Collection, Sort */}
            <Group gap="md">
              <TextInput
                placeholder="Search by title..."
                leftSection={<IconSearch size={16} />}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.currentTarget.value)}
                style={{ flex: 1, maxWidth: 300 }}
                size="sm"
              />
              <Group gap="xs">
                <Tooltip label={collectionFilterMode === 'include' ? 'Show only selected' : 'Hide selected'}>
                  <SegmentedControl
                    size="xs"
                    value={collectionFilterMode}
                    onChange={setCollectionFilterMode}
                    data={[
                      { value: 'include', label: 'Include' },
                      { value: 'exclude', label: 'Exclude' },
                    ]}
                    disabled={selectedCollections.length === 0}
                  />
                </Tooltip>
                <MultiSelect
                  placeholder={selectedCollections.length === 0 ? 'All Collections' : undefined}
                  data={collectionOptions}
                  value={selectedCollections}
                  onChange={setSelectedCollections}
                  style={{ minWidth: 200, maxWidth: 400 }}
                  size="sm"
                  clearable
                  searchable
                  maxDropdownHeight={200}
                />
              </Group>
              <Select
                placeholder="Sort by"
                value={sortBy}
                onChange={(val) => setSortBy(val || 'date_desc')}
                data={[
                  { value: 'date_desc', label: 'Date (Newest)' },
                  { value: 'date_asc', label: 'Date (Oldest)' },
                  { value: 'name_asc', label: 'Name (A-Z)' },
                  { value: 'name_desc', label: 'Name (Z-A)' },
                  { value: 'quality_desc', label: 'Quality (High-Low)' },
                ]}
                size="sm"
                style={{ width: 160 }}
              />
            </Group>

            {/* Row 2: Status Filters */}
            <Group gap="lg">
              <Group gap="xs">
                <Text size="xs" fw={500} c="dimmed">Review:</Text>
                <SegmentedControl
                  size="xs"
                  value={reviewFilter}
                  onChange={setReviewFilter}
                  data={[
                    { value: 'all', label: 'All' },
                    { value: 'reviewed', label: '✓ Reviewed' },
                    { value: 'not_reviewed', label: 'Not Reviewed' },
                  ]}
                />
              </Group>

              <Group gap="xs">
                <Text size="xs" fw={500} c="dimmed">Quality:</Text>
                <SegmentedControl
                  size="xs"
                  value={qualityFilter}
                  onChange={setQualityFilter}
                  data={[
                    { value: 'all', label: 'All' },
                    { value: 'high', label: 'High' },
                    { value: 'medium', label: 'Med' },
                    { value: 'low', label: 'Low' },
                  ]}
                />
              </Group>

              <Group gap="xs">
                <Text size="xs" fw={500} c="dimmed">Topic:</Text>
                <SegmentedControl
                  size="xs"
                  value={topicFilter}
                  onChange={setTopicFilter}
                  data={[
                    { value: 'all', label: 'All' },
                    { value: 'high', label: 'High' },
                    { value: 'medium', label: 'Med' },
                    { value: 'low', label: 'Low' },
                    { value: 'none', label: 'None' },
                  ]}
                />
              </Group>
            </Group>

            {/* Results count */}
            <Text size="xs" c="dimmed">
              Showing {filteredDocuments.length} of {documents.length} documents
            </Text>
          </Stack>
        </Paper>

        {/* Documents Grid */}
        {isLoading ? (
          <Box style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
            <Loader size="lg" color="amber" />
          </Box>
        ) : filteredDocuments.length === 0 ? (
          <Box
            style={{
              textAlign: 'center',
              padding: '60px 20px',
              color: 'var(--cream-dim)'
            }}
          >
            <IconFileText size={64} style={{ marginBottom: 16, opacity: 0.3 }} />
            <Text size="lg" mb={8}>
              {documents.length === 0 ? 'No documents yet' : 'No matching documents'}
            </Text>
            <Text size="sm" c="dimmed">
              {documents.length === 0
                ? (selectedCollections.length > 0
                    ? `No documents in selected collections`
                    : 'Add documents to get started')
                : 'Try adjusting your filters'}
            </Text>
          </Box>
        ) : (
          <>
          <Grid gutter="lg">
            {filteredDocuments.map((doc) => (
              <Grid.Col key={doc.id} span={{ base: 12, sm: 6, md: 4 }}>
                <Card
                  padding="lg"
                  radius="md"
                  style={{
                    background: 'var(--charcoal-light)',
                    border: '2px solid transparent',
                    borderLeftColor: 'var(--amber)',
                    borderLeftWidth: '4px',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    position: 'relative',
                  }}
                  onClick={() => handleViewDocument(doc.id)}
                  className="document-card"
                >
                  {/* Delete button - visible on hover */}
                  <Tooltip label="Delete document" position="top">
                    <ActionIcon
                      variant="subtle"
                      color="red"
                      size="sm"
                      onClick={(e) => handleDeleteClick(e, doc)}
                      style={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        opacity: 0,
                        transition: 'opacity 0.2s ease',
                      }}
                      className="delete-icon"
                    >
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Tooltip>

                  <Stack gap="sm">
                    <Group gap="xs" wrap="nowrap">
                      <IconFileText size={20} color="var(--amber)" />
                      <Text
                        size="md"
                        fw={600}
                        lineClamp={2}
                        style={{ color: 'var(--cream)', flex: 1 }}
                      >
                        {doc.filename}
                      </Text>
                    </Group>

                    {/* Status badges row */}
                    <Group gap="xs" wrap="wrap">
                      <Badge variant="light" color="amber" size="sm">
                        {doc.chunk_count} chunks
                      </Badge>

                      {doc.reviewed_by_human && (
                        <Tooltip label="Reviewed by human">
                          <Badge color="green" variant="light" size="sm" leftSection={<IconCheck size={10} />}>
                            Reviewed
                          </Badge>
                        </Tooltip>
                      )}

                      {doc.quality_score !== null && (
                        <Tooltip label={`Quality: ${(doc.quality_score * 100).toFixed(0)}%`}>
                          <Badge
                            color={doc.quality_score >= 0.7 ? 'green' : doc.quality_score >= 0.4 ? 'yellow' : 'red'}
                            variant="light"
                            size="sm"
                          >
                            Q: {(doc.quality_score * 100).toFixed(0)}%
                          </Badge>
                        </Tooltip>
                      )}

                      {doc.topic_relevance_score !== null && (
                        <Tooltip label={`Topic: ${doc.topic_provided || 'N/A'}`}>
                          <Badge
                            color={doc.topic_relevance_score >= 0.7 ? 'blue' : doc.topic_relevance_score >= 0.4 ? 'cyan' : 'gray'}
                            variant="light"
                            size="sm"
                          >
                            T: {(doc.topic_relevance_score * 100).toFixed(0)}%
                          </Badge>
                        </Tooltip>
                      )}
                    </Group>
                  </Stack>
                </Card>
              </Grid.Col>
            ))}
          </Grid>

          {/* Inline styles for hover effect */}
          <style>{`
            .document-card:hover .delete-icon {
              opacity: 1 !important;
            }
          `}</style>
          </>
        )}
      </Box>

      {/* Document Viewer Modal - Using shared DocumentModal component */}
      <DocumentModal
        document={viewingDocument}
        opened={isDocViewerOpen}
        onClose={() => {
          setIsDocViewerOpen(false);
          setViewingDocument(null);
        }}
        onDocumentUpdate={(updated) => {
          setViewingDocument(updated);
          // Also reload the documents list to reflect any changes
          loadDocuments();
        }}
      />

      {/* Ingestion Modal */}
      <IngestionModal
        opened={isIngestionModalOpen}
        onClose={() => {
          setIsIngestionModalOpen(false);
          loadDocuments(); // Reload documents after ingestion
        }}
        defaultCollection={selectedCollections.length === 1 ? selectedCollections[0] : undefined}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmDeleteModal
        opened={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false);
          setDeleteTarget(null);
        }}
        onConfirm={handleConfirmDelete}
        target={deleteTarget}
        isDeleting={isDeleting}
      />
    </>
  );
}
