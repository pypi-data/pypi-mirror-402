/**
 * DashboardView - Admin dashboard with system statistics and quality analytics
 *
 * Features:
 * - Stats cards showing system totals (collections, documents, chunks, storage)
 * - Quality score histogram
 * - Review status pie chart
 * - Collection filter for scoped analytics
 * - Quality comparison across collections
 * - Content composition (file types, ingest methods)
 * - Activity timeline and actor breakdown
 * - Crawl statistics
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Title,
  Select,
  Card,
  Text,
  Group,
  Loader,
  Stack,
  SimpleGrid,
  Alert,
  ActionIcon,
  Tooltip,
} from '@mantine/core';
import { IconAlertCircle, IconRefresh } from '@tabler/icons-react';
import { useRagStore } from '../../store';
import * as ragApi from '../../ragApi';
import type { AdminStats, QualityAnalytics, ContentAnalytics } from '../../ragApi';
import { StatsCards } from './StatsCards';
import { QualityHistogram } from './QualityHistogram';
import { ReviewStatusChart } from './ReviewStatusChart';
import { CollectionQualityChart } from './CollectionQualityChart';
import { FileTypeChart } from './FileTypeChart';
import { IngestMethodChart } from './IngestMethodChart';
import { ActorTypeChart } from './ActorTypeChart';
import { IngestionTimeline } from './IngestionTimeline';
import { CrawlStatsSection } from './CrawlStatsSection';

export function DashboardView() {
  const { collections, loadCollections } = useRagStore();
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  const [stats, setStats] = useState<AdminStats | null>(null);
  const [analytics, setAnalytics] = useState<QualityAnalytics | null>(null);
  const [contentAnalytics, setContentAnalytics] = useState<ContentAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load collections on mount
  useEffect(() => {
    loadCollections();
  }, []);

  // Load stats and analytics
  useEffect(() => {
    loadData();
  }, [selectedCollection]);

  // Auto-refresh polling: Fetch dashboard data every 10 seconds to reflect external changes
  useEffect(() => {
    const POLLING_INTERVAL = 10000; // 10 seconds

    const poll = async () => {
      if (!document.hidden) {
        try {
          const [statsData, analyticsData, contentData] = await Promise.all([
            ragApi.getAdminStats(selectedCollection || undefined),
            ragApi.getQualityAnalytics(selectedCollection || undefined),
            ragApi.getContentAnalytics(selectedCollection || undefined),
          ]);
          setStats(statsData);
          setAnalytics(analyticsData);
          setContentAnalytics(contentData);
        } catch (err) {
          console.error('[Polling] Failed to refresh dashboard:', err);
        }
      }
    };

    const intervalId = setInterval(poll, POLLING_INTERVAL);

    const handleVisibilityChange = () => {
      if (!document.hidden) {
        poll();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(intervalId);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [selectedCollection]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch all data in parallel
      const [statsData, analyticsData, contentData] = await Promise.all([
        ragApi.getAdminStats(selectedCollection || undefined),
        ragApi.getQualityAnalytics(selectedCollection || undefined),
        ragApi.getContentAnalytics(selectedCollection || undefined),
      ]);

      setStats(statsData);
      setAnalytics(analyticsData);
      setContentAnalytics(contentData);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  // Manual refresh handler
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const [statsData, analyticsData, contentData] = await Promise.all([
        ragApi.getAdminStats(selectedCollection || undefined),
        ragApi.getQualityAnalytics(selectedCollection || undefined),
        ragApi.getContentAnalytics(selectedCollection || undefined),
      ]);
      setStats(statsData);
      setAnalytics(analyticsData);
      setContentAnalytics(contentData);
    } catch (err) {
      console.error('Failed to refresh dashboard:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Prepare collection options for select
  const collectionOptions = [
    { value: '', label: 'All Collections' },
    ...collections.map((c) => ({ value: c.name, label: c.name })),
  ];

  if (error) {
    return (
      <Box style={{ animation: 'fadeIn 0.4s ease' }}>
        <Title order={2} mb="xl">Dashboard</Title>
        <Alert icon={<IconAlertCircle size={16} />} title="Error" color="red">
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box style={{ animation: 'fadeIn 0.4s ease' }}>
      {/* Header */}
      <Group justify="space-between" align="flex-start" mb="xl">
        <Group gap="sm">
          <Title order={2}>Dashboard</Title>
          <Tooltip label="Refresh data">
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

        <Select
          placeholder="Filter by collection"
          data={collectionOptions}
          value={selectedCollection || ''}
          onChange={(value) => setSelectedCollection(value || null)}
          clearable
          searchable
          w={250}
          styles={{
            input: {
              background: 'var(--charcoal-light)',
              borderColor: 'var(--charcoal-lighter)',
              color: 'var(--cream)',
            },
          }}
        />
      </Group>

      {isLoading ? (
        <Box style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
          <Loader color="amber" size="lg" />
        </Box>
      ) : (
        <Stack gap="xl">
          {/* Stats Cards (always system-wide) */}
          {stats && <StatsCards stats={stats} contentAnalytics={contentAnalytics} />}

          {/* Quality & Review Charts */}
          {analytics && (
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
              {/* Quality Histogram */}
              <Card
                padding="lg"
                style={{
                  background: 'var(--charcoal-light)',
                  border: '1px solid var(--charcoal-lighter)',
                }}
              >
                <Text size="lg" fw={600} mb="md" style={{ color: 'var(--cream)' }}>
                  Quality Score Distribution
                </Text>
                <QualityHistogram data={analytics.quality_histogram} />
              </Card>

              {/* Review Status Pie Chart */}
              <Card
                padding="lg"
                style={{
                  background: 'var(--charcoal-light)',
                  border: '1px solid var(--charcoal-lighter)',
                }}
              >
                <Text size="lg" fw={600} mb="md" style={{ color: 'var(--cream)' }}>
                  Review Status
                </Text>
                <ReviewStatusChart data={analytics.review_breakdown} />
              </Card>
            </SimpleGrid>
          )}

          {/* Content Composition Section */}
          {contentAnalytics && (
            <>
              <Text size="xl" fw={600} style={{ color: 'var(--cream)' }}>
                Content Composition
              </Text>
              <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
                {/* File Type Distribution */}
                <Card
                  padding="lg"
                  style={{
                    background: 'var(--charcoal-light)',
                    border: '1px solid var(--charcoal-lighter)',
                  }}
                >
                  <Text size="lg" fw={600} mb="md" style={{ color: 'var(--cream)' }}>
                    File Types
                  </Text>
                  <FileTypeChart data={contentAnalytics.file_type_distribution} />
                </Card>

                {/* Ingest Method Breakdown */}
                <Card
                  padding="lg"
                  style={{
                    background: 'var(--charcoal-light)',
                    border: '1px solid var(--charcoal-lighter)',
                  }}
                >
                  <Text size="lg" fw={600} mb="md" style={{ color: 'var(--cream)' }}>
                    Ingest Methods
                  </Text>
                  <IngestMethodChart data={contentAnalytics.ingest_method_breakdown} />
                </Card>
              </SimpleGrid>
            </>
          )}

          {/* Activity & Provenance Section */}
          {contentAnalytics && (
            <>
              <Text size="xl" fw={600} style={{ color: 'var(--cream)' }}>
                Activity & Provenance
              </Text>
              <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
                {/* Ingestion Timeline */}
                <Card
                  padding="lg"
                  style={{
                    background: 'var(--charcoal-light)',
                    border: '1px solid var(--charcoal-lighter)',
                  }}
                >
                  <Text size="lg" fw={600} mb="md" style={{ color: 'var(--cream)' }}>
                    Ingestion Activity (Last 30 Days)
                  </Text>
                  <IngestionTimeline data={contentAnalytics.ingestion_timeline} />
                </Card>

                {/* Actor Type Breakdown */}
                <Card
                  padding="lg"
                  style={{
                    background: 'var(--charcoal-light)',
                    border: '1px solid var(--charcoal-lighter)',
                  }}
                >
                  <Text size="lg" fw={600} mb="md" style={{ color: 'var(--cream)' }}>
                    Who Is Ingesting?
                  </Text>
                  <ActorTypeChart data={contentAnalytics.actor_type_breakdown} />
                </Card>
              </SimpleGrid>
            </>
          )}

          {/* Crawl Statistics Section */}
          {contentAnalytics && contentAnalytics.crawl_stats.total_crawl_sessions > 0 && (
            <>
              <Text size="xl" fw={600} style={{ color: 'var(--cream)' }}>
                Web Crawl Statistics
              </Text>
              <Card
                padding="lg"
                style={{
                  background: 'var(--charcoal-light)',
                  border: '1px solid var(--charcoal-lighter)',
                }}
              >
                <CrawlStatsSection data={contentAnalytics.crawl_stats} />
              </Card>
            </>
          )}

          {/* Quality by Collection (only when not filtered to a single collection) */}
          {analytics && analytics.quality_by_collection.length > 0 && !selectedCollection && (
            <Card
              padding="lg"
              style={{
                background: 'var(--charcoal-light)',
                border: '1px solid var(--charcoal-lighter)',
              }}
            >
              <Text size="lg" fw={600} mb="md" style={{ color: 'var(--cream)' }}>
                Quality by Collection
              </Text>
              <CollectionQualityChart data={analytics.quality_by_collection} />
            </Card>
          )}

          {/* Topic Relevance Histogram */}
          {analytics && (
            <Card
              padding="lg"
              style={{
                background: 'var(--charcoal-light)',
                border: '1px solid var(--charcoal-lighter)',
              }}
            >
              <Text size="lg" fw={600} mb="md" style={{ color: 'var(--cream)' }}>
                Topic Relevance Distribution
              </Text>
              <QualityHistogram data={analytics.topic_histogram} color="#14b8a6" />
            </Card>
          )}
        </Stack>
      )}
    </Box>
  );
}
