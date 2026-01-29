/**
 * SearchResults - Display RAG semantic search results with similarity scores
 */

import { Stack, Card, Text, Group, Badge, Progress, Anchor } from '@mantine/core';
import { IconSearch, IconFile } from '@tabler/icons-react';
import type { SearchResult } from '../types';

interface SearchResultsProps {
  results: SearchResult[];
  onDocumentClick?: (documentId: number) => void;
}

export default function SearchResults({
  results,
  onDocumentClick,
}: SearchResultsProps) {
  if (!Array.isArray(results) || results.length === 0) {
    return null;
  }

  return (
    <Card shadow="sm" p="md" radius="md" withBorder mt="md">
      <Stack gap="md">
        <Group gap="xs">
          <IconSearch size={18} />
          <Text fw={500} size="sm">
            Search Results ({results.length})
          </Text>
        </Group>

        {results.map((result, index) => {
          const similarityPercent = Math.round(result.similarity * 100);
          const colorMap = {
            excellent: 'green',
            good: 'blue',
            moderate: 'yellow',
            weak: 'gray',
          };
          const getQuality = (score: number) => {
            if (score >= 0.6) return 'excellent';
            if (score >= 0.4) return 'good';
            if (score >= 0.25) return 'moderate';
            return 'weak';
          };
          const quality = getQuality(result.similarity);

          return (
            <Card key={index} shadow="xs" p="sm" radius="sm" withBorder>
              <Stack gap="xs">
                {/* Document info */}
                <Group justify="space-between">
                  {onDocumentClick ? (
                    <Anchor
                      size="sm"
                      fw={500}
                      onClick={() => onDocumentClick(result.source_document_id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <Group gap="xs">
                        <IconFile size={14} />
                        {result.source_filename}
                      </Group>
                    </Anchor>
                  ) : (
                    <Group gap="xs">
                      <IconFile size={14} />
                      <Text size="sm" fw={500}>
                        {result.source_filename}
                      </Text>
                    </Group>
                  )}
                  <Badge variant="light" color={colorMap[quality]} size="sm">
                    {similarityPercent}% match
                  </Badge>
                </Group>

                {/* Similarity bar */}
                <Progress
                  value={similarityPercent}
                  color={colorMap[quality]}
                  size="xs"
                />

                {/* Content preview */}
                <Text size="xs" c="dimmed" lineClamp={3}>
                  {result.content}
                </Text>

                {/* Metadata */}
                {result.chunk_index !== undefined && (
                  <Text size="xs" c="dimmed">
                    Chunk {result.chunk_index + 1}
                  </Text>
                )}
              </Stack>
            </Card>
          );
        })}
      </Stack>
    </Card>
  );
}
