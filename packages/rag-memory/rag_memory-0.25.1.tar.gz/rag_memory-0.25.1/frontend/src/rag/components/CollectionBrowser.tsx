/**
 * CollectionBrowser - Left sidebar for browsing and managing collections
 */

import { useState, useEffect, useMemo } from 'react';
import {
  Stack,
  Card,
  Text,
  Title,
  Button,
  Badge,
  Group,
  ActionIcon,
  Modal,
  TextInput,
  Textarea,
  ScrollArea,
  Loader,
  Divider,
  Box,
  Pagination,
  Table,
  Tooltip,
  SegmentedControl,
  Select,
  Paper,
} from '@mantine/core';
import {
  IconPlus,
  IconDatabase,
  IconLink,
  IconFileText,
  IconList,
  IconEye,
  IconTrash,
  IconSearch,
  IconCheck,
  IconRefresh,
} from '@tabler/icons-react';
import { useRagStore } from '../store';
import * as ragApi from '../ragApi';
import type { CollectionInfo, CollectionMetadataSchema, DocumentListItemDetailed, Document } from '../types';
import DocumentModal from './DocumentModal';
import { ConfirmDeleteModal, DeleteTarget } from './modals/ConfirmDeleteModal';

export default function CollectionBrowser() {
  const {
    collections,
    selectedCollectionId,
    selectCollection,
    createCollection,
    loadCollections,
  } = useRagStore();

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Expose modal trigger via window global so LeftNavigation can open it
  useEffect(() => {
    console.log('CollectionBrowser: Setting up window.__openCreateCollectionModal');
    (window as any).__openCreateCollectionModal = () => {
      console.log('CollectionBrowser: Modal trigger called via window global');
      setIsCreateModalOpen(true);
    };

    // Cleanup on unmount
    return () => {
      console.log('CollectionBrowser: Cleaning up window.__openCreateCollectionModal');
      delete (window as any).__openCreateCollectionModal;
    };
  }, []);

  // Auto-refresh polling: Fetch collections every 10 seconds to reflect external changes
  // (e.g., collections created via MCP tools, CLI, or other clients)
  useEffect(() => {
    const POLLING_INTERVAL = 10000; // 10 seconds

    const poll = () => {
      // Only poll if the document is visible (save resources when tab is hidden)
      if (!document.hidden) {
        loadCollections();
      }
    };

    // Set up interval
    const intervalId = setInterval(poll, POLLING_INTERVAL);

    // Also poll when tab becomes visible again
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadCollections();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Cleanup on unmount
    return () => {
      clearInterval(intervalId);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [loadCollections]);

  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [selectedCollectionInfo, setSelectedCollectionInfo] = useState<CollectionInfo | null>(null);
  const [metadataSchema, setMetadataSchema] = useState<CollectionMetadataSchema | null>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [newCollection, setNewCollection] = useState({
    name: '',
    description: '',
    domain: '',
    domainScope: '',
  });

  // All documents modal state
  const [isAllDocsModalOpen, setIsAllDocsModalOpen] = useState(false);
  const [allDocuments, setAllDocuments] = useState<DocumentListItemDetailed[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const docsPerPage = 20;

  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [reviewFilter, setReviewFilter] = useState<string>('all'); // 'all' | 'reviewed' | 'not_reviewed'
  const [qualityFilter, setQualityFilter] = useState<string>('all'); // 'all' | 'high' | 'medium' | 'low'
  const [topicFilter, setTopicFilter] = useState<string>('all'); // 'all' | 'high' | 'medium' | 'low' | 'none'
  const [sortBy, setSortBy] = useState<string>('date_desc'); // 'date_desc' | 'date_asc' | 'name_asc' | 'name_desc' | 'quality_desc'

  // Document viewer modal state
  const [isDocViewerOpen, setIsDocViewerOpen] = useState(false);
  const [viewingDocument, setViewingDocument] = useState<Document | null>(null);

  // Delete collection modal state
  const [isDeleteCollectionModalOpen, setIsDeleteCollectionModalOpen] = useState(false);
  const [deleteCollectionTarget, setDeleteCollectionTarget] = useState<DeleteTarget | null>(null);
  const [isDeletingCollection, setIsDeletingCollection] = useState(false);

  // Manual refresh state
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Manual refresh handler
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await loadCollections();
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleCollectionClick = async (collection: any) => {
    setIsDetailsModalOpen(true);
    setIsLoadingDetails(true);
    setMetadataSchema(null);
    selectCollection(collection.name);

    try {
      // Fetch collection info and metadata schema in parallel
      const [fullInfo, schema] = await Promise.all([
        ragApi.getCollectionInfo(collection.name),
        ragApi.getCollectionMetadataSchema(collection.name).catch(() => null),
      ]);
      setSelectedCollectionInfo(fullInfo);
      setMetadataSchema(schema);
    } catch (error) {
      console.error('Failed to load collection details:', error);
      setSelectedCollectionInfo(null);
      setMetadataSchema(null);
    } finally {
      setIsLoadingDetails(false);
    }
  };

  const handleCreateCollection = async () => {
    try {
      await createCollection(
        newCollection.name,
        newCollection.description,
        newCollection.domain,
        newCollection.domainScope
      );
      setIsCreateModalOpen(false);
      setNewCollection({ name: '', description: '', domain: '', domainScope: '' });
      loadCollections();
    } catch (error) {
      console.error('Failed to create collection:', error);
    }
  };

  const handleViewAllDocuments = async () => {
    if (!selectedCollectionInfo) return;

    setIsAllDocsModalOpen(true);
    setIsLoadingDocs(true);
    setCurrentPage(1);
    // Reset filters when opening modal
    setSearchQuery('');
    setReviewFilter('all');
    setQualityFilter('all');
    setTopicFilter('all');
    setSortBy('date_desc');

    try {
      // Fetch all documents for this collection with full details
      const docs = await ragApi.listDocuments(selectedCollectionInfo.name, 1000, 0, true);
      setAllDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
      setAllDocuments([]);
    } finally {
      setIsLoadingDocs(false);
    }
  };

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

  const handleViewDocumentByFilename = async (filename: string) => {
    if (!selectedCollectionInfo) return;

    // Find the document ID by filename
    const docs = await ragApi.listDocuments(selectedCollectionInfo.name, 1000, 0);
    const doc = docs.find(d => d.filename === filename);
    if (doc) {
      handleViewDocument(doc.id);
    }
  };

  // Filter and sort documents
  const filteredDocuments = useMemo(() => {
    let filtered = [...allDocuments];

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
  }, [allDocuments, searchQuery, reviewFilter, qualityFilter, topicFilter, sortBy]);

  // Pagination
  const totalPages = Math.ceil(filteredDocuments.length / docsPerPage);
  const getCurrentPageDocuments = () => {
    const startIdx = (currentPage - 1) * docsPerPage;
    const endIdx = startIdx + docsPerPage;
    return filteredDocuments.slice(startIdx, endIdx);
  };

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, reviewFilter, qualityFilter, topicFilter, sortBy]);

  const handleDeleteCollectionClick = () => {
    if (!selectedCollectionInfo) return;

    setDeleteCollectionTarget({
      type: 'collection',
      name: selectedCollectionInfo.name,
      documentCount: selectedCollectionInfo.document_count,
    });
    setIsDeleteCollectionModalOpen(true);
  };

  const handleConfirmDeleteCollection = async () => {
    if (!deleteCollectionTarget) return;

    setIsDeletingCollection(true);
    try {
      await ragApi.deleteCollection(deleteCollectionTarget.name);
      // Close modals
      setIsDeleteCollectionModalOpen(false);
      setIsDetailsModalOpen(false);
      setDeleteCollectionTarget(null);
      setSelectedCollectionInfo(null);
      // Reload collections list
      loadCollections();
    } catch (error) {
      console.error('Failed to delete collection:', error);
    } finally {
      setIsDeletingCollection(false);
    }
  };

  return (
    <>
      <Card shadow="sm" p="md" radius="md" withBorder h="100%">
        <Stack gap="md" h="100%">
          {/* Header */}
          <Group justify="space-between">
            <Group gap="xs">
              <Title order={4}>Collections</Title>
              <Tooltip label="Refresh collections">
                <ActionIcon
                  variant="subtle"
                  color="gray"
                  onClick={handleRefresh}
                  loading={isRefreshing}
                  size="sm"
                >
                  <IconRefresh size={16} />
                </ActionIcon>
              </Tooltip>
            </Group>
            <ActionIcon
              variant="light"
              color="blue"
              onClick={() => setIsCreateModalOpen(true)}
              title="Create collection"
            >
              <IconPlus size={18} />
            </ActionIcon>
          </Group>

          {/* Collections list */}
          <ScrollArea style={{ flex: 1 }}>
            <Stack gap="xs">
              {collections.length === 0 ? (
                <Text c="dimmed" size="sm" ta="center" mt="md">
                  No collections yet
                </Text>
              ) : (
                collections.map((collection) => (
                  <Card
                    key={collection.name}
                    padding="sm"
                    radius="md"
                    withBorder
                    style={{
                      cursor: 'pointer',
                      backgroundColor:
                        selectedCollectionId === collection.name
                          ? 'var(--mantine-color-blue-9)'
                          : undefined,
                    }}
                    onClick={() => handleCollectionClick(collection)}
                  >
                    <Group justify="space-between" mb="xs">
                      <Group gap="xs">
                        <IconDatabase size={16} />
                        <Text fw={500} size="sm">
                          {collection.name}
                        </Text>
                      </Group>
                    </Group>

                    <Text size="xs" c="dimmed" lineClamp={2}>
                      {collection.description}
                    </Text>

                    {collection.domain && (
                      <Badge variant="light" size="xs" mt="xs">
                        {collection.domain}
                      </Badge>
                    )}
                  </Card>
                ))
              )}
            </Stack>
          </ScrollArea>
        </Stack>
      </Card>

      {/* Create Collection Modal */}
      <Modal
        opened={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Collection"
        size="md"
      >
        <Stack gap="md">
          <TextInput
            label="Name"
            placeholder="api-docs"
            required
            value={newCollection.name}
            onChange={(e) =>
              setNewCollection({ ...newCollection, name: e.currentTarget.value })
            }
          />

          <Textarea
            label="Description"
            placeholder="API documentation and guides"
            required
            value={newCollection.description}
            onChange={(e) =>
              setNewCollection({ ...newCollection, description: e.currentTarget.value })
            }
          />

          <TextInput
            label="Domain"
            placeholder="engineering"
            required
            value={newCollection.domain}
            onChange={(e) =>
              setNewCollection({ ...newCollection, domain: e.currentTarget.value })
            }
          />

          <Textarea
            label="Domain Scope"
            placeholder="Internal API documentation"
            required
            value={newCollection.domainScope}
            onChange={(e) =>
              setNewCollection({
                ...newCollection,
                domainScope: e.currentTarget.value,
              })
            }
          />

          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateCollection}
              disabled={
                !newCollection.name ||
                !newCollection.description ||
                !newCollection.domain ||
                !newCollection.domainScope
              }
            >
              Create
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Collection Details Modal */}
      <Modal
        opened={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        title="Collection Details"
        size="xl"
      >
        {isLoadingDetails ? (
          <Box style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
            <Loader size="lg" />
          </Box>
        ) : selectedCollectionInfo ? (
          <ScrollArea h="calc(90vh - 120px)" offsetScrollbars>
            <Stack gap="lg" p="xs">
              {/* Basic Information */}
              <div>
                <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb="xs">
                  Basic Information
                </Text>
                <Stack gap="md">
                  <div>
                    <Text size="sm" fw={600} c="dimmed" mb={4}>
                      Name
                    </Text>
                    <Text size="sm" fw={500}>{selectedCollectionInfo.name}</Text>
                  </div>

                  <div>
                    <Text size="sm" fw={600} c="dimmed" mb={4}>
                      Description
                    </Text>
                    <Text size="sm">{selectedCollectionInfo.description}</Text>
                  </div>

                  {selectedCollectionInfo.domain && (
                    <div>
                      <Text size="sm" fw={600} c="dimmed" mb={4}>
                        Domain
                      </Text>
                      <Badge variant="light" size="lg">{selectedCollectionInfo.domain}</Badge>
                    </div>
                  )}

                  {selectedCollectionInfo.domain_scope && (
                    <div>
                      <Text size="sm" fw={600} c="dimmed" mb={4}>
                        Domain Scope
                      </Text>
                      <Text size="sm">{selectedCollectionInfo.domain_scope}</Text>
                    </div>
                  )}

                  <div>
                    <Text size="sm" fw={600} c="dimmed" mb={4}>
                      Created
                    </Text>
                    <Text size="sm">
                      {new Date(selectedCollectionInfo.created_at).toLocaleString()}
                    </Text>
                  </div>
                </Stack>
              </div>

              <Divider />

              {/* Statistics */}
              <div>
                <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb="xs">
                  Statistics
                </Text>
                <Group gap="xl">
                  <div>
                    <Text size="sm" fw={600} c="dimmed" mb={4}>
                      Documents
                    </Text>
                    <Text size="xl" fw={700} c="blue">
                      {selectedCollectionInfo.document_count}
                    </Text>
                  </div>

                  <div>
                    <Text size="sm" fw={600} c="dimmed" mb={4}>
                      Chunks
                    </Text>
                    <Text size="xl" fw={700} c="blue">
                      {selectedCollectionInfo.chunk_count}
                    </Text>
                  </div>
                </Group>
              </div>

              {/* Metadata Schema - only show if there are custom fields */}
              {metadataSchema && metadataSchema.custom_fields && Object.keys(metadataSchema.custom_fields).length > 0 && (
                <>
                  <Divider />
                  <div>
                    <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb="xs">
                      Custom Metadata Fields
                    </Text>
                    <Table withTableBorder withColumnBorders>
                      <Table.Thead>
                        <Table.Tr>
                          <Table.Th>Field Name</Table.Th>
                          <Table.Th>Type</Table.Th>
                          <Table.Th>Constraints</Table.Th>
                        </Table.Tr>
                      </Table.Thead>
                      <Table.Tbody>
                        {Object.entries(metadataSchema.custom_fields).map(([fieldName, fieldDef]) => (
                          <Table.Tr key={fieldName}>
                            <Table.Td>
                              <Text size="sm" fw={500}>{fieldName}</Text>
                              {fieldDef.description && (
                                <Text size="xs" c="dimmed">{fieldDef.description}</Text>
                              )}
                            </Table.Td>
                            <Table.Td>
                              <Badge variant="light" size="sm">{fieldDef.type}</Badge>
                            </Table.Td>
                            <Table.Td>
                              <Group gap="xs">
                                {fieldDef.required && (
                                  <Badge color="red" variant="light" size="xs">required</Badge>
                                )}
                                {fieldDef.enum && fieldDef.enum.length > 0 && (
                                  <Tooltip label={`Values: ${fieldDef.enum.join(', ')}`}>
                                    <Badge color="blue" variant="light" size="xs">
                                      enum ({fieldDef.enum.length})
                                    </Badge>
                                  </Tooltip>
                                )}
                                {!fieldDef.required && (!fieldDef.enum || fieldDef.enum.length === 0) && (
                                  <Text size="xs" c="dimmed">—</Text>
                                )}
                              </Group>
                            </Table.Td>
                          </Table.Tr>
                        ))}
                      </Table.Tbody>
                    </Table>
                    {metadataSchema.system_fields && metadataSchema.system_fields.length > 0 && (
                      <Text size="xs" c="dimmed" mt="xs">
                        System fields: {metadataSchema.system_fields.join(', ')}
                      </Text>
                    )}
                  </div>
                </>
              )}

              {/* Sample Documents */}
              {selectedCollectionInfo.sample_documents && selectedCollectionInfo.sample_documents.length > 0 && (
                <>
                  <Divider />
                  <div>
                    <Group justify="space-between" mb="xs">
                      <Text size="xs" fw={700} c="dimmed" tt="uppercase">
                        Sample Documents ({selectedCollectionInfo.sample_documents.length})
                      </Text>
                      {selectedCollectionInfo.document_count > selectedCollectionInfo.sample_documents.length && (
                        <Button
                          variant="light"
                          size="xs"
                          leftSection={<IconList size={14} />}
                          onClick={handleViewAllDocuments}
                        >
                          View All {selectedCollectionInfo.document_count} Documents
                        </Button>
                      )}
                    </Group>
                    <Stack gap="xs">
                      {selectedCollectionInfo.sample_documents.map((filename, idx) => (
                        <Card
                          key={`doc-${idx}-${filename}`}
                          padding="xs"
                          radius="sm"
                          withBorder
                          style={{ cursor: 'pointer' }}
                          onClick={() => handleViewDocumentByFilename(filename)}
                        >
                          <Group gap="xs" wrap="nowrap" justify="space-between">
                            <Group gap="xs" wrap="nowrap" style={{ flex: 1 }}>
                              <IconFileText size={16} style={{ flexShrink: 0 }} />
                              <Text size="sm" fw={500} lineClamp={2} style={{ flex: 1 }}>
                                {filename}
                              </Text>
                            </Group>
                            <Tooltip label="View document">
                              <ActionIcon variant="subtle" size="sm">
                                <IconEye size={14} />
                              </ActionIcon>
                            </Tooltip>
                          </Group>
                        </Card>
                      ))}
                    </Stack>
                  </div>
                </>
              )}

              {/* Crawled URLs */}
              {selectedCollectionInfo.crawled_urls && selectedCollectionInfo.crawled_urls.length > 0 && (
                <>
                  <Divider />
                  <div>
                    <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb="xs">
                      Crawled URLs ({selectedCollectionInfo.crawled_urls.length})
                    </Text>
                    <ScrollArea h={200} offsetScrollbars>
                      <Stack gap="xs" pr="xs">
                        {selectedCollectionInfo.crawled_urls.map((urlData, idx) => (
                          <Card key={`${urlData.url}-${idx}`} padding="xs" radius="sm" withBorder>
                            <Stack gap={4}>
                              <Group gap="xs" wrap="nowrap">
                                <IconLink size={14} style={{ flexShrink: 0 }} />
                                <Text
                                  size="xs"
                                  style={{
                                    wordBreak: 'break-all',
                                    flex: 1,
                                  }}
                                  component="a"
                                  href={urlData.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  c="blue"
                                >
                                  {urlData.url}
                                </Text>
                              </Group>
                              <Group gap="md" pl="20px">
                                <Text size="xs" c="dimmed">
                                  {urlData.page_count} page{urlData.page_count !== 1 ? 's' : ''}
                                </Text>
                                <Text size="xs" c="dimmed">
                                  {urlData.chunk_count} chunk{urlData.chunk_count !== 1 ? 's' : ''}
                                </Text>
                                <Text size="xs" c="dimmed">
                                  {new Date(urlData.timestamp).toLocaleDateString()}
                                </Text>
                              </Group>
                            </Stack>
                          </Card>
                        ))}
                      </Stack>
                    </ScrollArea>
                  </div>
                </>
              )}

              <Divider />

              {/* Actions */}
              <Group justify="space-between">
                <Button
                  color="red"
                  variant="light"
                  leftSection={<IconTrash size={16} />}
                  onClick={handleDeleteCollectionClick}
                >
                  Delete Collection
                </Button>
                <Button variant="light" onClick={() => setIsDetailsModalOpen(false)}>
                  Close
                </Button>
              </Group>
            </Stack>
          </ScrollArea>
        ) : (
          <Text size="sm" c="dimmed" ta="center" py="xl">
            Failed to load collection details
          </Text>
        )}
      </Modal>

      {/* All Documents Modal */}
      <Modal
        opened={isAllDocsModalOpen}
        onClose={() => setIsAllDocsModalOpen(false)}
        title={
          selectedCollectionInfo
            ? `All Documents - ${selectedCollectionInfo.name}`
            : 'All Documents'
        }
        size="90%"
      >
        {isLoadingDocs ? (
          <Box style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
            <Loader size="lg" />
          </Box>
        ) : allDocuments.length > 0 ? (
          <Stack gap="md">
            {/* Filter Bar */}
            <Paper p="sm" withBorder>
              <Stack gap="sm">
                {/* Row 1: Search and Sort */}
                <Group gap="md">
                  <TextInput
                    placeholder="Search by title..."
                    leftSection={<IconSearch size={16} />}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.currentTarget.value)}
                    style={{ flex: 1, maxWidth: 300 }}
                    size="sm"
                  />
                  <Select
                    label="Sort by"
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

                {/* Row 2: Filters */}
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
                  Showing {filteredDocuments.length} of {allDocuments.length} documents
                </Text>
              </Stack>
            </Paper>

            {/* Documents Table */}
            <ScrollArea h="calc(90vh - 350px)" offsetScrollbars>
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Document</Table.Th>
                    <Table.Th style={{ width: '80px', textAlign: 'center' }}>
                      <Tooltip label="Human reviewed">
                        <span>Review</span>
                      </Tooltip>
                    </Table.Th>
                    <Table.Th style={{ width: '90px', textAlign: 'center' }}>
                      <Tooltip label="Content quality score (0-1)">
                        <span>Quality</span>
                      </Tooltip>
                    </Table.Th>
                    <Table.Th style={{ width: '90px', textAlign: 'center' }}>
                      <Tooltip label="Topic relevance score (0-1)">
                        <span>Topic</span>
                      </Tooltip>
                    </Table.Th>
                    <Table.Th style={{ width: '100px', textAlign: 'center' }}>Date</Table.Th>
                    <Table.Th style={{ width: '70px', textAlign: 'center' }}>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {getCurrentPageDocuments().map((doc) => (
                    <Table.Tr key={doc.id}>
                      <Table.Td>
                        <Group gap="xs" wrap="nowrap">
                          <IconFileText size={16} style={{ flexShrink: 0 }} />
                          <Tooltip label={doc.filename} disabled={doc.filename.length < 50}>
                            <Text size="sm" lineClamp={1} style={{ flex: 1 }}>
                              {doc.filename}
                            </Text>
                          </Tooltip>
                        </Group>
                      </Table.Td>
                      <Table.Td style={{ textAlign: 'center' }}>
                        {doc.reviewed_by_human ? (
                          <Tooltip label="Reviewed by human">
                            <Badge color="green" variant="light" size="sm" leftSection={<IconCheck size={12} />}>
                              Yes
                            </Badge>
                          </Tooltip>
                        ) : (
                          <Badge color="gray" variant="light" size="sm">
                            No
                          </Badge>
                        )}
                      </Table.Td>
                      <Table.Td style={{ textAlign: 'center' }}>
                        {doc.quality_score !== null ? (
                          <Tooltip label={`Quality: ${(doc.quality_score * 100).toFixed(0)}%`}>
                            <Badge
                              color={doc.quality_score >= 0.7 ? 'green' : doc.quality_score >= 0.4 ? 'yellow' : 'red'}
                              variant="light"
                              size="sm"
                            >
                              {(doc.quality_score * 100).toFixed(0)}%
                            </Badge>
                          </Tooltip>
                        ) : (
                          <Text size="xs" c="dimmed">—</Text>
                        )}
                      </Table.Td>
                      <Table.Td style={{ textAlign: 'center' }}>
                        {doc.topic_relevance_score !== null ? (
                          <Tooltip label={`Topic: ${doc.topic_provided || 'Unknown'}`}>
                            <Badge
                              color={doc.topic_relevance_score >= 0.7 ? 'blue' : doc.topic_relevance_score >= 0.4 ? 'cyan' : 'gray'}
                              variant="light"
                              size="sm"
                            >
                              {(doc.topic_relevance_score * 100).toFixed(0)}%
                            </Badge>
                          </Tooltip>
                        ) : (
                          <Text size="xs" c="dimmed">—</Text>
                        )}
                      </Table.Td>
                      <Table.Td style={{ textAlign: 'center' }}>
                        <Text size="xs" c="dimmed">
                          {new Date(doc.created_at).toLocaleDateString()}
                        </Text>
                      </Table.Td>
                      <Table.Td style={{ textAlign: 'center' }}>
                        <Tooltip label="View document">
                          <ActionIcon
                            variant="light"
                            color="blue"
                            onClick={() => handleViewDocument(doc.id)}
                          >
                            <IconEye size={16} />
                          </ActionIcon>
                        </Tooltip>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </ScrollArea>

            {/* Pagination and Close */}
            <Group justify="space-between">
              {totalPages > 1 ? (
                <Pagination
                  total={totalPages}
                  value={currentPage}
                  onChange={setCurrentPage}
                  size="sm"
                />
              ) : (
                <div />
              )}
              <Button variant="light" onClick={() => setIsAllDocsModalOpen(false)}>
                Close
              </Button>
            </Group>
          </Stack>
        ) : (
          <Text size="sm" c="dimmed" ta="center" py="xl">
            No documents found
          </Text>
        )}
      </Modal>

      {/* Document Viewer Modal - Using shared DocumentModal component */}
      <DocumentModal
        document={viewingDocument}
        opened={isDocViewerOpen}
        onClose={() => {
          setIsDocViewerOpen(false);
          setViewingDocument(null);
        }}
        onDocumentUpdate={(updated) => setViewingDocument(updated)}
      />

      {/* Delete Collection Confirmation Modal */}
      <ConfirmDeleteModal
        opened={isDeleteCollectionModalOpen}
        onClose={() => {
          setIsDeleteCollectionModalOpen(false);
          setDeleteCollectionTarget(null);
        }}
        onConfirm={handleConfirmDeleteCollection}
        target={deleteCollectionTarget}
        isDeleting={isDeletingCollection}
      />
    </>
  );
}
