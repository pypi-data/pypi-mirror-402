/**
 * PageRelevanceDisplay - Shows relevance scores and LLM reasoning for dry-run preview
 *
 * Features:
 * - Color-coded score badges (green/yellow/red)
 * - Recommendation badges
 * - Expandable detailed reasoning
 * - Handles single and multiple pages
 */

import { useState } from 'react';
import {
  Paper,
  Stack,
  Group,
  Text,
  Badge,
  Button,
  Divider,
  ScrollArea,
} from '@mantine/core';
import { IconChevronDown, IconChevronUp, IconAlertCircle, IconCheck, IconX } from '@tabler/icons-react';

interface PageData {
  url: string;
  title: string;
  status_code: number | null;
  relevance_score: number | null;
  relevance_summary: string | null;
  recommendation: 'ingest' | 'review' | 'skip';
  reason?: string; // Only for HTTP errors
}

interface PageRelevanceDisplayProps {
  pages: PageData[];
  topic: string;
  pagesRecommended: number;
  pagesToReview: number;
  pagesToSkip: number;
  pagesFailed: number;
}

function getScoreColor(score: number | null): string {
  if (score === null) return 'gray';
  if (score >= 0.5) return 'teal';
  if (score >= 0.4) return 'yellow';
  return 'red';
}

function getRecommendationIcon(recommendation: string) {
  switch (recommendation) {
    case 'ingest':
      return <IconCheck size={16} />;
    case 'review':
      return <IconAlertCircle size={16} />;
    case 'skip':
      return <IconX size={16} />;
    default:
      return null;
  }
}

function getRecommendationColor(recommendation: string): string {
  switch (recommendation) {
    case 'ingest':
      return 'teal';
    case 'review':
      return 'yellow';
    case 'skip':
      return 'red';
    default:
      return 'gray';
  }
}

function SinglePageDisplay({ page }: { page: PageData }) {
  const [expanded, setExpanded] = useState(false);

  // HTTP error case
  if (page.reason) {
    return (
      <Paper
        p="md"
        style={{
          background: 'var(--charcoal-light)',
          border: '2px solid #ef4444',
        }}
      >
        <Group gap="xs" mb="sm">
          <IconX size={20} color="#ef4444" />
          <Text fw={600} size="sm" style={{ color: '#ef4444' }}>
            Cannot Ingest Page
          </Text>
        </Group>
        <Stack gap="xs">
          <Text size="sm" c="cream" fw={500}>
            {page.title}
          </Text>
          <Text size="sm" c="dimmed">
            {page.reason}
          </Text>
        </Stack>
      </Paper>
    );
  }

  const scoreColor = getScoreColor(page.relevance_score);
  const recommendationColor = getRecommendationColor(page.recommendation);

  return (
    <Paper
      p="md"
      style={{
        background: 'var(--charcoal-light)',
        border: `2px solid ${scoreColor === 'teal' ? 'var(--teal)' : scoreColor === 'yellow' ? '#f59e0b' : '#ef4444'}`,
      }}
    >
      <Stack gap="sm">
        <Group justify="space-between" wrap="nowrap">
          <Text fw={600} size="sm" c="cream" style={{ flex: 1 }}>
            {page.title}
          </Text>
        </Group>

        <Group gap="sm">
          <Badge color={scoreColor} variant="light" size="lg">
            Relevance: {page.relevance_score !== null ? `${Math.round(page.relevance_score * 100)}%` : 'N/A'}
          </Badge>
          <Badge color={recommendationColor} variant="light" size="lg" leftSection={getRecommendationIcon(page.recommendation)}>
            {page.recommendation === 'ingest' ? 'Recommended' : page.recommendation === 'review' ? 'Review' : 'Not Recommended'}
          </Badge>
        </Group>

        {page.relevance_summary && (
          <>
            <Divider />
            <Text size="sm" c="dimmed">
              {expanded ? page.relevance_summary : `${page.relevance_summary.slice(0, 100)}${page.relevance_summary.length > 100 ? '...' : ''}`}
            </Text>
            {page.relevance_summary.length > 100 && (
              <Button
                variant="subtle"
                size="xs"
                onClick={() => setExpanded(!expanded)}
                rightSection={expanded ? <IconChevronUp size={14} /> : <IconChevronDown size={14} />}
              >
                {expanded ? 'Show less' : 'Show detailed reasoning'}
              </Button>
            )}
          </>
        )}

        {page.recommendation === 'skip' && (
          <>
            <Divider />
            <Text size="xs" c="yellow" fw={500}>
              ⚠ Low relevance score. You can still ingest if needed.
            </Text>
          </>
        )}
      </Stack>
    </Paper>
  );
}

function MultiPageDisplay({ pages, pagesRecommended, pagesToReview, pagesToSkip, pagesFailed }: Omit<PageRelevanceDisplayProps, 'topic'>) {
  const [expandedPages, setExpandedPages] = useState<Set<number>>(new Set());

  const toggleExpand = (index: number) => {
    const newExpanded = new Set(expandedPages);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedPages(newExpanded);
  };

  // Determine overall status
  const hasRecommended = pagesRecommended > 0;
  const allFailed = pagesFailed === pages.length && pages.length > 0;

  return (
    <Paper
      p="md"
      style={{
        background: 'var(--charcoal-light)',
        border: `2px solid ${hasRecommended ? 'var(--teal)' : allFailed ? '#ef4444' : '#f59e0b'}`,
      }}
    >
      <Stack gap="md">
        {/* Summary Header */}
        <Group gap="xs">
          {hasRecommended ? (
            <IconCheck size={20} color="var(--teal)" />
          ) : allFailed ? (
            <IconX size={20} color="#ef4444" />
          ) : (
            <IconAlertCircle size={20} color="#f59e0b" />
          )}
          <Text fw={600} size="sm" style={{ color: hasRecommended ? 'var(--teal)' : allFailed ? '#ef4444' : '#f59e0b' }}>
            {allFailed ? 'All Pages Failed' : hasRecommended ? 'Pages Found' : 'Review Needed'}
          </Text>
        </Group>

        <Group gap="lg">
          {pagesRecommended > 0 && (
            <div>
              <Text size="xs" c="dimmed" mb={4}>Recommended</Text>
              <Badge color="teal" variant="light" size="lg">
                {pagesRecommended} pages
              </Badge>
            </div>
          )}
          {pagesToReview > 0 && (
            <div>
              <Text size="xs" c="dimmed" mb={4}>Need Review</Text>
              <Badge color="yellow" variant="light" size="lg">
                {pagesToReview} pages
              </Badge>
            </div>
          )}
          {pagesToSkip > 0 && (
            <div>
              <Text size="xs" c="dimmed" mb={4}>Not Recommended</Text>
              <Badge color="red" variant="light" size="lg">
                {pagesToSkip} pages
              </Badge>
            </div>
          )}
          {pagesFailed > 0 && (
            <div>
              <Text size="xs" c="dimmed" mb={4}>Failed</Text>
              <Badge color="gray" variant="light" size="lg">
                {pagesFailed} pages
              </Badge>
            </div>
          )}
        </Group>

        <Divider />

        {/* Page List */}
        <ScrollArea h={300} type="auto">
          <Stack gap="xs">
            {pages.map((page, idx) => {
              const isExpanded = expandedPages.has(idx);
              const scoreColor = getScoreColor(page.relevance_score);
              const recommendationColor = getRecommendationColor(page.recommendation);

              return (
                <Paper
                  key={idx}
                  p="sm"
                  style={{
                    background: 'var(--charcoal)',
                    border: `1px solid ${scoreColor === 'teal' ? 'var(--teal)' : scoreColor === 'yellow' ? '#f59e0b' : scoreColor === 'red' ? '#ef4444' : 'var(--warm-gray)'}`,
                  }}
                >
                  <Stack gap="xs">
                    <Group justify="space-between" wrap="nowrap">
                      <Text size="sm" fw={500} c="cream" lineClamp={1} style={{ flex: 1 }}>
                        {page.title}
                      </Text>
                      <Group gap="xs">
                        {page.relevance_score !== null && (
                          <Badge color={scoreColor} variant="light" size="sm">
                            {Math.round(page.relevance_score * 100)}%
                          </Badge>
                        )}
                        <Badge color={recommendationColor} variant="light" size="sm">
                          {page.recommendation}
                        </Badge>
                      </Group>
                    </Group>

                    {page.reason ? (
                      <Text size="xs" c="red">
                        {page.reason}
                      </Text>
                    ) : page.relevance_summary ? (
                      <>
                        <Text size="xs" c="dimmed" lineClamp={isExpanded ? undefined : 2}>
                          {page.relevance_summary}
                        </Text>
                        {page.relevance_summary.length > 100 && (
                          <Button
                            variant="subtle"
                            size="xs"
                            onClick={() => toggleExpand(idx)}
                            rightSection={isExpanded ? <IconChevronUp size={12} /> : <IconChevronDown size={12} />}
                          >
                            {isExpanded ? 'Less' : 'More'}
                          </Button>
                        )}
                      </>
                    ) : null}
                  </Stack>
                </Paper>
              );
            })}
          </Stack>
        </ScrollArea>

        <Divider />

        {/* Footer Message */}
        {hasRecommended ? (
          <Text size="sm" c="teal" fw={500}>
            ✓ Found {pagesRecommended} relevant page{pagesRecommended !== 1 ? 's' : ''}. Click below to proceed with ingestion.
          </Text>
        ) : allFailed ? (
          <Text size="sm" c="red" fw={500}>
            ✗ All pages failed. Cannot proceed with ingestion.
          </Text>
        ) : (
          <Text size="sm" c="yellow" fw={500}>
            ⚠ No highly relevant pages found. You can still ingest if needed (button below).
          </Text>
        )}
      </Stack>
    </Paper>
  );
}

export function PageRelevanceDisplay(props: PageRelevanceDisplayProps) {
  const isSinglePage = props.pages.length === 1;

  return isSinglePage ? (
    <SinglePageDisplay page={props.pages[0]} />
  ) : (
    <MultiPageDisplay {...props} />
  );
}
