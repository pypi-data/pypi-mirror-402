/**
 * TemporalTimeline - Display temporal knowledge evolution timeline
 */

import { Stack, Card, Text, Group, Badge } from '@mantine/core';
import { IconTimeline } from '@tabler/icons-react';
import type { TemporalResult } from '../types';

interface TemporalTimelineProps {
  timeline: TemporalResult[];
}

export default function TemporalTimeline({ timeline }: TemporalTimelineProps) {
  if (!timeline || timeline.length === 0) {
    return null;
  }

  // Sort by valid_from date (most recent first)
  const sorted = [...timeline].sort((a, b) =>
    new Date(b.valid_from).getTime() - new Date(a.valid_from).getTime()
  );

  return (
    <Card shadow="sm" p="md" radius="md" withBorder mt="md">
      <Stack gap="md">
        <Group gap="xs">
          <IconTimeline size={18} />
          <Text fw={500} size="sm">
            Knowledge Evolution Timeline
          </Text>
        </Group>

        {sorted.map((fact, index) => (
          <Card
            key={index}
            shadow="xs"
            p="sm"
            radius="sm"
            withBorder
            style={{
              borderLeft:
                fact.status === 'current'
                  ? '4px solid var(--mantine-color-green-6)'
                  : '4px solid var(--mantine-color-gray-6)',
            }}
          >
            <Stack gap="xs">
              {/* Status badge and date range */}
              <Group justify="space-between">
                <Badge
                  variant="light"
                  color={fact.status === 'current' ? 'green' : 'gray'}
                  size="sm"
                >
                  {fact.status}
                </Badge>
                <Text size="xs" c="dimmed">
                  {new Date(fact.valid_from).toLocaleDateString()} -{' '}
                  {fact.valid_until
                    ? new Date(fact.valid_until).toLocaleDateString()
                    : 'Present'}
                </Text>
              </Group>

              {/* Fact content */}
              <Text size="sm">{fact.fact}</Text>

              {/* Relationship type */}
              <Text size="xs" c="dimmed" fs="italic">
                {fact.relationship_type}
              </Text>
            </Stack>
          </Card>
        ))}
      </Stack>
    </Card>
  );
}
