/**
 * SearchView - Three-tab search interface (Semantic | Relationships | Temporal)
 *
 * Features:
 * - Tab system with animated underline
 * - Each tab: query input + collection scope + search button
 * - Results display with amber score badges
 * - Staggered slide-in animations
 */

import { useState } from 'react';
import {
  Box,
  Title,
  Tabs,
  Textarea,
  Select,
  Button,
  Card,
  Text,
  Group,
  Badge,
  Stack,
  ScrollArea,
  Slider,
  Tooltip,
} from '@mantine/core';
import { IconSearch, IconChartDots, IconClock, IconEye } from '@tabler/icons-react';
import { useRagStore } from '../../store';
import * as ragApi from '../../ragApi';
import type { Document } from '../../types';
import { GraphVisualization } from '../visualizations/GraphVisualization';
import { TimelineVisualization } from '../visualizations/TimelineVisualization';
import DocumentModal from '../DocumentModal';

interface SearchResult {
  content: string;
  similarity?: number;
  source_filename: string;
  source_document_id: number;
}

interface Relationship {
  id: string;
  relationship_type: string;
  fact: string;
  source_node_id: string;
  target_node_id: string;
  source_node_name?: string;
  target_node_name?: string;
}

interface TemporalItem {
  fact: string;
  relationship_type: string;
  source_node_id?: string;
  target_node_id?: string;
  source_node_name?: string;
  target_node_name?: string;
  valid_from: string;
  valid_until: string | null;
  status: 'current' | 'superseded';
  created_at?: string;
  expired_at?: string | null;
}

export function SearchView() {
  const { collections } = useRagStore();
  const [activeTab, setActiveTab] = useState<string>('semantic');

  // Common state
  const [query, setQuery] = useState('');
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [threshold, setThreshold] = useState(0.35); // Default matches MCP server default

  // Results state
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [temporalItems, setTemporalItems] = useState<TemporalItem[]>([]);

  // Visualization modals state
  const [isGraphModalOpen, setIsGraphModalOpen] = useState(false);
  const [isTimelineModalOpen, setIsTimelineModalOpen] = useState(false);

  // Document viewer modal state
  const [isDocViewerOpen, setIsDocViewerOpen] = useState(false);
  const [viewingDocument, setViewingDocument] = useState<Document | null>(null);

  const collectionOptions = [
    { label: 'All Collections', value: '' },
    ...collections.map(c => ({ label: c.name, value: c.name }))
  ];

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

  const handleSemanticSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const results = await ragApi.searchDocuments({
        query,
        collectionName: selectedCollection || undefined,
        limit: 10,
        threshold,
      });
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleRelationshipSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const results = await ragApi.queryRelationships(
        query,
        selectedCollection || undefined,
        10,
        threshold
      );
      setRelationships(results);
    } catch (error) {
      console.error('Relationship query failed:', error);
      setRelationships([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleTemporalSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const results = await ragApi.queryTemporal(
        query,
        selectedCollection || undefined,
        10,
        threshold
      );
      setTemporalItems(results);
    } catch (error) {
      console.error('Temporal query failed:', error);
      setTemporalItems([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearch = () => {
    switch (activeTab) {
      case 'semantic':
        handleSemanticSearch();
        break;
      case 'relationships':
        handleRelationshipSearch();
        break;
      case 'temporal':
        handleTemporalSearch();
        break;
    }
  };

  return (
    <Box style={{ animation: 'fadeIn 0.4s ease' }}>
      {/* Header */}
      <Title
        order={2}
        mb={24}
        style={{
          fontFamily: 'Playfair Display, Georgia, serif',
          fontWeight: 700,
          background: 'linear-gradient(135deg, var(--amber-light), var(--amber))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}
      >
        Search
      </Title>

      <Tabs value={activeTab} onChange={(value) => value && setActiveTab(value)}>
        <Tabs.List
          style={{
            borderBottom: '2px solid var(--amber-dark)',
            marginBottom: 24
          }}
        >
          <Tabs.Tab
            value="semantic"
            leftSection={<IconSearch size={16} />}
            style={{
              color: activeTab === 'semantic' ? 'var(--amber)' : 'var(--cream-dim)',
              fontWeight: activeTab === 'semantic' ? 600 : 400,
              transition: 'all 0.3s ease'
            }}
          >
            Semantic
          </Tabs.Tab>
          <Tabs.Tab
            value="relationships"
            leftSection={<IconChartDots size={16} />}
            style={{
              color: activeTab === 'relationships' ? 'var(--amber)' : 'var(--cream-dim)',
              fontWeight: activeTab === 'relationships' ? 600 : 400,
              transition: 'all 0.3s ease'
            }}
          >
            Relationships
          </Tabs.Tab>
          <Tabs.Tab
            value="temporal"
            leftSection={<IconClock size={16} />}
            style={{
              color: activeTab === 'temporal' ? 'var(--amber)' : 'var(--cream-dim)',
              fontWeight: activeTab === 'temporal' ? 600 : 400,
              transition: 'all 0.3s ease'
            }}
          >
            Temporal
          </Tabs.Tab>
        </Tabs.List>

        {/* Semantic Search */}
        <Tabs.Panel value="semantic">
          <Stack gap="lg">
            {/* Search Form */}
            <Card
              padding="lg"
              radius="md"
              style={{
                background: 'var(--charcoal-light)',
                border: '2px solid var(--amber-dark)'
              }}
            >
              <Stack gap="md">
                <Textarea
                  placeholder="What are you looking for? (e.g., 'How do I implement authentication?')"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  minRows={3}
                  styles={{
                    input: {
                      background: 'var(--charcoal)',
                      border: '1px solid var(--warm-gray)',
                      color: 'var(--cream)'
                    }
                  }}
                />

                <Group align="flex-end">
                  <Select
                    placeholder="Collection (optional)"
                    data={collectionOptions}
                    value={selectedCollection || ''}
                    onChange={(value) => setSelectedCollection(value || null)}
                    style={{ flex: 1 }}
                    clearable
                  />

                  <Tooltip label={`Min similarity: ${(threshold * 100).toFixed(0)}%`}>
                    <Box style={{ width: 120 }}>
                      <Text size="xs" c="dimmed" mb={4}>Threshold</Text>
                      <Slider
                        value={threshold}
                        onChange={setThreshold}
                        min={0}
                        max={1}
                        step={0.05}
                        marks={[
                          { value: 0.25, label: '25%' },
                          { value: 0.5, label: '50%' },
                          { value: 0.75, label: '75%' },
                        ]}
                        color="amber"
                        size="sm"
                        styles={{
                          markLabel: { fontSize: 10, color: 'var(--warm-gray)' }
                        }}
                      />
                    </Box>
                  </Tooltip>

                  <Button
                    leftSection={<IconSearch size={18} />}
                    onClick={handleSearch}
                    disabled={!query.trim() || isSearching}
                    loading={isSearching}
                    color="amber"
                    style={{
                      background: 'linear-gradient(135deg, var(--amber) 0%, var(--amber-dark) 100%)',
                    }}
                  >
                    Search
                  </Button>
                </Group>
              </Stack>
            </Card>

            {/* Results */}
            {searchResults.length > 0 && (
              <ScrollArea h="calc(100vh - 400px)">
                <Stack gap="md">
                  {searchResults.map((result, idx) => (
                    <Card
                      key={`${result.source_document_id}-${idx}`}
                      padding="lg"
                      radius="md"
                      onClick={() => handleViewDocument(result.source_document_id)}
                      style={{
                        background: 'var(--charcoal-light)',
                        border: '2px solid transparent',
                        borderLeftColor: 'var(--amber)',
                        borderLeftWidth: '4px',
                        animation: `slideIn 0.4s ease ${idx * 0.1}s both`,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                      }}
                      className="search-result-card"
                    >
                      <Stack gap="sm">
                        <Group justify="space-between">
                          <Text
                            size="sm"
                            fw={600}
                            style={{ color: 'var(--amber)' }}
                          >
                            {result.source_filename}
                          </Text>
                          {result.similarity !== undefined && (
                            <Badge
                              variant="filled"
                              color="amber"
                              size="lg"
                            >
                              {(result.similarity * 100).toFixed(0)}% match
                            </Badge>
                          )}
                        </Group>

                        <Text
                          size="sm"
                          style={{
                            color: 'var(--cream)',
                            lineHeight: 1.6
                          }}
                        >
                          {result.content}
                        </Text>
                      </Stack>
                    </Card>
                  ))}
                </Stack>
              </ScrollArea>
            )}
          </Stack>
        </Tabs.Panel>

        {/* Relationships Search */}
        <Tabs.Panel value="relationships">
          <Stack gap="lg">
            {/* Search Form */}
            <Card
              padding="lg"
              radius="md"
              style={{
                background: 'var(--charcoal-light)',
                border: '2px solid var(--teal)'
              }}
            >
              <Stack gap="md">
                <Textarea
                  placeholder="Explore connections (e.g., 'How does X relate to Y?')"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  minRows={3}
                  styles={{
                    input: {
                      background: 'var(--charcoal)',
                      border: '1px solid var(--warm-gray)',
                      color: 'var(--cream)'
                    }
                  }}
                />

                <Group align="flex-end">
                  <Select
                    placeholder="Collection (optional)"
                    data={collectionOptions}
                    value={selectedCollection || ''}
                    onChange={(value) => setSelectedCollection(value || null)}
                    style={{ flex: 1 }}
                    clearable
                  />

                  <Tooltip label={`Min relevance: ${(threshold * 100).toFixed(0)}%`}>
                    <Box style={{ width: 120 }}>
                      <Text size="xs" c="dimmed" mb={4}>Threshold</Text>
                      <Slider
                        value={threshold}
                        onChange={setThreshold}
                        min={0}
                        max={1}
                        step={0.05}
                        marks={[
                          { value: 0.25, label: '25%' },
                          { value: 0.5, label: '50%' },
                          { value: 0.75, label: '75%' },
                        ]}
                        color="teal"
                        size="sm"
                        styles={{
                          markLabel: { fontSize: 10, color: 'var(--warm-gray)' }
                        }}
                      />
                    </Box>
                  </Tooltip>

                  <Button
                    leftSection={<IconChartDots size={18} />}
                    onClick={handleSearch}
                    disabled={!query.trim() || isSearching}
                    loading={isSearching}
                    color="teal"
                  >
                    Query Graph
                  </Button>
                </Group>
              </Stack>
            </Card>

            {/* Visualize Button */}
            {relationships.length > 0 && (
              <Button
                leftSection={<IconEye size={18} />}
                onClick={() => {
                  console.log('SearchView: Opening graph modal with relationships:', relationships);
                  console.log('SearchView: Relationship count:', relationships.length);
                  setIsGraphModalOpen(true);
                }}
                variant="light"
                color="teal"
                size="md"
                style={{
                  background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.1), rgba(15, 118, 110, 0.1))',
                  border: '1px solid var(--teal)'
                }}
              >
                Visualize Graph
              </Button>
            )}

            {/* Results */}
            {relationships.length > 0 && (
              <ScrollArea h="calc(100vh - 400px)">
                <Stack gap="md">
                  {relationships.map((rel, idx) => (
                    <Card
                      key={rel.id}
                      padding="lg"
                      radius="md"
                      style={{
                        background: 'var(--charcoal-light)',
                        border: '2px solid transparent',
                        borderLeftColor: 'var(--teal)',
                        borderLeftWidth: '4px',
                        animation: `slideIn 0.4s ease ${idx * 0.1}s both`
                      }}
                    >
                      <Stack gap="sm">
                        <Badge variant="light" color="teal" size="md">
                          {rel.relationship_type}
                        </Badge>

                        <Text
                          size="sm"
                          style={{
                            color: 'var(--cream)',
                            lineHeight: 1.6
                          }}
                        >
                          {rel.fact}
                        </Text>

                        <Group gap="xs">
                          <Text size="xs" c="dimmed">From:</Text>
                          <Badge variant="outline" color="teal" size="xs">
                            {rel.source_node_name || rel.source_node_id}
                          </Badge>
                          <Text size="xs" c="dimmed">→</Text>
                          <Badge variant="outline" color="teal" size="xs">
                            {rel.target_node_name || rel.target_node_id}
                          </Badge>
                        </Group>
                      </Stack>
                    </Card>
                  ))}
                </Stack>
              </ScrollArea>
            )}
          </Stack>
        </Tabs.Panel>

        {/* Temporal Search */}
        <Tabs.Panel value="temporal">
          <Stack gap="lg">
            {/* Search Form */}
            <Card
              padding="lg"
              radius="md"
              style={{
                background: 'var(--charcoal-light)',
                border: '2px solid var(--sienna)'
              }}
            >
              <Stack gap="md">
                <Textarea
                  placeholder="Track evolution (e.g., 'How has X changed over time?')"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  minRows={3}
                  styles={{
                    input: {
                      background: 'var(--charcoal)',
                      border: '1px solid var(--warm-gray)',
                      color: 'var(--cream)'
                    }
                  }}
                />

                <Group align="flex-end">
                  <Select
                    placeholder="Collection (optional)"
                    data={collectionOptions}
                    value={selectedCollection || ''}
                    onChange={(value) => setSelectedCollection(value || null)}
                    style={{ flex: 1 }}
                    clearable
                  />

                  <Tooltip label={`Min relevance: ${(threshold * 100).toFixed(0)}%`}>
                    <Box style={{ width: 120 }}>
                      <Text size="xs" c="dimmed" mb={4}>Threshold</Text>
                      <Slider
                        value={threshold}
                        onChange={setThreshold}
                        min={0}
                        max={1}
                        step={0.05}
                        marks={[
                          { value: 0.25, label: '25%' },
                          { value: 0.5, label: '50%' },
                          { value: 0.75, label: '75%' },
                        ]}
                        color="orange"
                        size="sm"
                        styles={{
                          markLabel: { fontSize: 10, color: 'var(--warm-gray)' }
                        }}
                      />
                    </Box>
                  </Tooltip>

                  <Button
                    leftSection={<IconClock size={18} />}
                    onClick={handleSearch}
                    disabled={!query.trim() || isSearching}
                    loading={isSearching}
                    style={{
                      background: 'var(--sienna)'
                    }}
                  >
                    Query Timeline
                  </Button>
                </Group>
              </Stack>
            </Card>

            {/* Visualize Button */}
            {temporalItems.length > 0 && (
              <Button
                leftSection={<IconEye size={18} />}
                onClick={() => setIsTimelineModalOpen(true)}
                variant="light"
                color="orange"
                size="md"
                style={{
                  background: 'linear-gradient(135deg, rgba(234, 88, 12, 0.1), rgba(217, 119, 6, 0.1))',
                  border: '1px solid var(--sienna)'
                }}
              >
                Visualize Timeline
              </Button>
            )}

            {/* Results */}
            {temporalItems.length > 0 && (
              <ScrollArea h="calc(100vh - 400px)">
                <Stack gap="md">
                  {temporalItems.map((item, idx) => (
                    <Card
                      key={idx}
                      padding="lg"
                      radius="md"
                      style={{
                        background: 'var(--charcoal-light)',
                        border: '2px solid transparent',
                        borderLeftColor: 'var(--sienna)',
                        borderLeftWidth: '4px',
                        animation: `slideIn 0.4s ease ${idx * 0.1}s both`
                      }}
                    >
                      <Stack gap="sm">
                        <Group justify="space-between">
                          <Badge variant="light" style={{ background: 'var(--sienna)' }} size="md">
                            {item.relationship_type}
                          </Badge>
                          <Badge
                            variant="outline"
                            color={item.status === 'current' ? 'teal' : 'gray'}
                            size="sm"
                          >
                            {item.status}
                          </Badge>
                        </Group>

                        <Text
                          size="sm"
                          style={{
                            color: 'var(--cream)',
                            lineHeight: 1.6
                          }}
                        >
                          {item.fact}
                        </Text>

                        {(item.source_node_name || item.target_node_name) && (
                          <Group gap="xs">
                            <Text size="xs" c="dimmed">Entities:</Text>
                            {item.source_node_name && (
                              <Badge variant="outline" color="orange" size="xs">
                                {item.source_node_name}
                              </Badge>
                            )}
                            {item.source_node_name && item.target_node_name && (
                              <Text size="xs" c="dimmed">→</Text>
                            )}
                            {item.target_node_name && (
                              <Badge variant="outline" color="orange" size="xs">
                                {item.target_node_name}
                              </Badge>
                            )}
                          </Group>
                        )}

                        <Group gap="md" mt="xs">
                          <div>
                            <Text size="xs" c="dimmed" mb={2}>Valid From</Text>
                            <Text size="xs" c="cream">
                              {new Date(item.valid_from).toLocaleDateString()}
                            </Text>
                          </div>
                          {item.valid_until && (
                            <div>
                              <Text size="xs" c="dimmed" mb={2}>Valid Until</Text>
                              <Text size="xs" c="cream">
                                {new Date(item.valid_until).toLocaleDateString()}
                              </Text>
                            </div>
                          )}
                        </Group>
                      </Stack>
                    </Card>
                  ))}
                </Stack>
              </ScrollArea>
            )}
          </Stack>
        </Tabs.Panel>
      </Tabs>

      {/* Empty State (when no results yet) */}
      {!isSearching && activeTab === 'semantic' && searchResults.length === 0 && query === '' && (
        <Box
          style={{
            textAlign: 'center',
            padding: '80px 20px',
            color: 'var(--cream-dim)'
          }}
        >
          <IconSearch size={64} style={{ marginBottom: 16, opacity: 0.3 }} />
          <Text size="lg" mb={8}>Search your knowledge base</Text>
          <Text size="sm" c="dimmed">
            Enter a natural language question to find relevant documents
          </Text>
        </Box>
      )}

      {/* Visualization Modals */}
      <GraphVisualization
        relationships={relationships}
        opened={isGraphModalOpen}
        onClose={() => setIsGraphModalOpen(false)}
      />
      <TimelineVisualization
        items={temporalItems}
        opened={isTimelineModalOpen}
        onClose={() => setIsTimelineModalOpen(false)}
      />

      {/* Document Viewer Modal */}
      <DocumentModal
        document={viewingDocument}
        opened={isDocViewerOpen}
        onClose={() => {
          setIsDocViewerOpen(false);
          setViewingDocument(null);
        }}
        onDocumentUpdate={(updated) => {
          setViewingDocument(updated);
        }}
      />

      {/* Hover styles for search result cards */}
      <style>{`
        .search-result-card:hover {
          border-color: var(--amber) !important;
          transform: translateX(4px);
        }
      `}</style>
    </Box>
  );
}
