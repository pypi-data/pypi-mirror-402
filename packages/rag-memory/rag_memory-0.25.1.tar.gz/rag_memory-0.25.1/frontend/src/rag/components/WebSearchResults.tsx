/**
 * WebSearchResults - Display web search results with clickable URLs and actions
 */

import { Stack, Card, Text, Group, Badge, Anchor, Button } from '@mantine/core';
import { IconWorld, IconCheck, IconDownload } from '@tabler/icons-react';
import type { WebSearchResult } from '../types';

interface WebSearchResultsProps {
  results: WebSearchResult[];
  onValidateUrl?: (url: string) => void;
  onIngestUrl?: (url: string) => void;
}

export default function WebSearchResults({
  results,
  onValidateUrl,
  onIngestUrl,
}: WebSearchResultsProps) {
  if (!results || results.length === 0) {
    return null;
  }

  return (
    <Card shadow="sm" p="md" radius="md" withBorder mt="md">
      <Stack gap="md">
        <Group gap="xs">
          <IconWorld size={18} />
          <Text fw={500} size="sm">
            Web Search Results ({results.length})
          </Text>
        </Group>

        {results.map((result, index) => (
          <Card key={index} shadow="xs" p="sm" radius="sm" withBorder>
            <Stack gap="xs">
              {/* Title with clickable link */}
              <Anchor
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                fw={500}
                size="sm"
              >
                {result.title}
              </Anchor>

              {/* Snippet */}
              <Text size="xs" c="dimmed" lineClamp={2}>
                {result.snippet}
              </Text>

              {/* URL and source */}
              <Group justify="space-between">
                <Text size="xs" c="dimmed" truncate style={{ maxWidth: '60%' }}>
                  {result.url}
                </Text>
                {result.source && (
                  <Badge variant="light" size="xs">
                    {result.source}
                  </Badge>
                )}
              </Group>

              {/* Action buttons */}
              {(onValidateUrl || onIngestUrl) && (
                <Group gap="xs" mt="xs">
                  {onValidateUrl && (
                    <Button
                      size="xs"
                      variant="light"
                      leftSection={<IconCheck size={14} />}
                      onClick={() => onValidateUrl(result.url)}
                    >
                      Validate
                    </Button>
                  )}
                  {onIngestUrl && (
                    <Button
                      size="xs"
                      variant="light"
                      color="blue"
                      leftSection={<IconDownload size={14} />}
                      onClick={() => onIngestUrl(result.url)}
                    >
                      Ingest
                    </Button>
                  )}
                </Group>
              )}
            </Stack>
          </Card>
        ))}
      </Stack>
    </Card>
  );
}
