/**
 * IngestionTimeline - Stacked area chart showing ingestion activity over time
 */

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';

interface TimelineData {
  date: string;
  total: number;
  url: number;
  file: number;
  text: number;
  directory: number;
}

interface Props {
  data: TimelineData[];
}

// Color palette for ingest methods (stacked)
const METHOD_COLORS = {
  url: '#0f766e',      // teal
  file: '#f59e0b',     // amber
  text: '#6366f1',     // indigo
  directory: '#8b5cf6', // violet
};

export function IngestionTimeline({ data }: Props) {
  // If no data, show placeholder
  if (data.length === 0) {
    return (
      <div
        style={{
          height: 280,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--warm-gray)',
        }}
      >
        No activity in the last 30 days
      </div>
    );
  }

  // Reverse data to show oldest first (left to right)
  const chartData = [...data].reverse().map((d) => ({
    ...d,
    // Format date for display
    displayDate: new Date(d.date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--charcoal-lighter)" />
        <XAxis
          dataKey="displayDate"
          stroke="var(--warm-gray)"
          fontSize={11}
          tickLine={false}
          interval="preserveStartEnd"
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
          labelStyle={{ color: 'var(--cream)', fontWeight: 600 }}
          formatter={(value, name) => {
            const labels: Record<string, string> = {
              url: 'URL Crawl',
              file: 'File Upload',
              text: 'Text Paste',
              directory: 'Directory',
            };
            return [`${value}`, labels[name as string] || name];
          }}
        />
        <Legend
          verticalAlign="top"
          height={36}
          formatter={(value) => {
            const labels: Record<string, string> = {
              url: 'URL',
              file: 'File',
              text: 'Text',
              directory: 'Dir',
            };
            return <span style={{ color: 'var(--cream)', fontSize: 11 }}>{labels[value] || value}</span>;
          }}
        />
        <Area
          type="monotone"
          dataKey="url"
          stackId="1"
          stroke={METHOD_COLORS.url}
          fill={METHOD_COLORS.url}
          fillOpacity={0.8}
        />
        <Area
          type="monotone"
          dataKey="file"
          stackId="1"
          stroke={METHOD_COLORS.file}
          fill={METHOD_COLORS.file}
          fillOpacity={0.8}
        />
        <Area
          type="monotone"
          dataKey="text"
          stackId="1"
          stroke={METHOD_COLORS.text}
          fill={METHOD_COLORS.text}
          fillOpacity={0.8}
        />
        <Area
          type="monotone"
          dataKey="directory"
          stackId="1"
          stroke={METHOD_COLORS.directory}
          fill={METHOD_COLORS.directory}
          fillOpacity={0.8}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
