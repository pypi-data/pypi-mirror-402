/**
 * StatsCards - Display system-wide statistics in a row of cards
 */

import { Card, Text, Group, SimpleGrid, ThemeIcon } from '@mantine/core';
import { IconStack, IconFileText, IconPuzzle, IconChartBar } from '@tabler/icons-react';
import type { AdminStats, ContentAnalytics } from '../../ragApi';

interface Props {
  stats: AdminStats;
  contentAnalytics?: ContentAnalytics | null;
}

export function StatsCards({ stats, contentAnalytics }: Props) {
  // Build subtitle for Documents card - include storage size if available
  const docsSubtitle = contentAnalytics?.storage
    ? `${stats.documents.reviewed} reviewed • ${contentAnalytics.storage.total_human}`
    : `${stats.documents.reviewed} reviewed`;

  // Build subtitle for Chunks card - include avg per doc if available
  const chunksSubtitle = contentAnalytics?.chunks
    ? `~${contentAnalytics.chunks.avg_per_doc} avg per doc`
    : undefined;

  const cards = [
    {
      title: 'Collections',
      value: stats.collections.total,
      icon: IconStack,
      color: '#f59e0b', // amber
    },
    {
      title: 'Documents',
      value: stats.documents.total,
      subtitle: docsSubtitle,
      icon: IconFileText,
      color: '#14b8a6', // teal
    },
    {
      title: 'Chunks',
      value: stats.chunks.total,
      subtitle: chunksSubtitle,
      icon: IconPuzzle,
      color: '#6366f1', // indigo
    },
    {
      title: 'Avg Quality',
      value: stats.quality.avg !== null ? `${Math.round(stats.quality.avg * 100)}%` : 'N/A',
      subtitle: stats.quality.distribution.high + stats.quality.distribution.medium + stats.quality.distribution.low > 0
        ? `${stats.quality.distribution.high} high, ${stats.quality.distribution.medium} med, ${stats.quality.distribution.low} low`
        : undefined,
      icon: IconChartBar,
      color: '#10b981', // emerald
    },
  ];

  return (
    <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="md">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card
            key={card.title}
            padding="lg"
            style={{
              background: 'var(--charcoal-light)',
              border: '1px solid var(--charcoal-lighter)',
              transition: 'all 0.2s ease',
            }}
            className="card-hover"
          >
            <Group justify="space-between" align="flex-start">
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                  {card.title}
                </Text>
                <Text
                  size="xl"
                  fw={700}
                  mt={4}
                  style={{ color: 'var(--cream)', fontSize: '2rem' }}
                >
                  {typeof card.value === 'number' ? card.value.toLocaleString() : card.value}
                </Text>
                {card.subtitle && (
                  <Text size="xs" c="dimmed" mt={4}>
                    {card.subtitle}
                  </Text>
                )}
              </div>
              <ThemeIcon
                size={48}
                radius="md"
                variant="light"
                style={{
                  backgroundColor: `${card.color}20`,
                  color: card.color,
                }}
              >
                <Icon size={24} />
              </ThemeIcon>
            </Group>
          </Card>
        );
      })}
    </SimpleGrid>
  );
}
