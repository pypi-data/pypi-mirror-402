/**
 * CrawlStatsSection - Domain table and crawl depth chart
 */

import { Box, Text, Table, Badge } from '@mantine/core';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface DomainData {
  domain: string;
  page_count: number;
  avg_quality: number | null;
}

interface DepthData {
  depth: number;
  count: number;
  label: string;
}

interface CrawlStats {
  domains: DomainData[];
  depth_distribution: DepthData[];
  total_crawl_sessions: number;
}

interface Props {
  data: CrawlStats;
}

export function CrawlStatsSection({ data }: Props) {
  const hasDomains = data.domains.length > 0;
  const hasDepth = data.depth_distribution.length > 0;

  // If no crawl data at all, show placeholder
  if (!hasDomains && !hasDepth && data.total_crawl_sessions === 0) {
    return (
      <div
        style={{
          height: 200,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--warm-gray)',
        }}
      >
        No web crawl data available
      </div>
    );
  }

  return (
    <Box style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
      {/* Domains Table */}
      <Box style={{ flex: '1 1 350px', minWidth: 300 }}>
        <Text size="sm" c="dimmed" mb="xs">
          Top Crawled Domains ({data.total_crawl_sessions} sessions)
        </Text>
        {hasDomains ? (
          <Table
            striped
            highlightOnHover
            styles={{
              table: { backgroundColor: 'var(--charcoal)' },
              tr: { borderColor: 'var(--charcoal-lighter)' },
              td: { color: 'var(--cream)', padding: '8px 12px', fontSize: 13 },
              th: { color: 'var(--warm-gray)', padding: '8px 12px', fontSize: 12, fontWeight: 500 },
            }}
          >
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Domain</Table.Th>
                <Table.Th style={{ textAlign: 'right' }}>Pages</Table.Th>
                <Table.Th style={{ textAlign: 'right' }}>Quality</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {data.domains.slice(0, 5).map((d) => (
                <Table.Tr key={d.domain}>
                  <Table.Td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {d.domain}
                  </Table.Td>
                  <Table.Td style={{ textAlign: 'right' }}>{d.page_count}</Table.Td>
                  <Table.Td style={{ textAlign: 'right' }}>
                    {d.avg_quality !== null ? (
                      <Badge
                        size="sm"
                        color={d.avg_quality >= 0.7 ? 'teal' : d.avg_quality >= 0.4 ? 'yellow' : 'red'}
                        variant="light"
                      >
                        {Math.round(d.avg_quality * 100)}%
                      </Badge>
                    ) : (
                      <span style={{ color: 'var(--warm-gray)' }}>-</span>
                    )}
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        ) : (
          <Text c="dimmed" size="sm">No domains crawled yet</Text>
        )}
      </Box>

      {/* Depth Distribution Chart */}
      <Box style={{ flex: '1 1 250px', minWidth: 200 }}>
        <Text size="sm" c="dimmed" mb="xs">
          Crawl Depth Distribution
        </Text>
        {hasDepth ? (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data.depth_distribution} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--charcoal-lighter)" />
              <XAxis
                dataKey="label"
                stroke="var(--warm-gray)"
                fontSize={11}
                tickLine={false}
              />
              <YAxis
                stroke="var(--warm-gray)"
                fontSize={12}
                tickLine={false}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--charcoal)',
                  border: '1px solid var(--charcoal-lighter)',
                  borderRadius: 8,
                }}
                itemStyle={{ color: 'var(--cream)' }}
                labelStyle={{ color: 'var(--cream)' }}
                formatter={(value) => [`${value} pages`, 'Count']}
              />
              <Bar
                dataKey="count"
                fill="#0f766e"
                radius={[4, 4, 0, 0]}
                maxBarSize={50}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Text c="dimmed" size="sm">No depth data</Text>
        )}
      </Box>
    </Box>
  );
}
