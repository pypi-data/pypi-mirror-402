/**
 * IngestMethodChart - Donut chart showing how content is ingested
 */

import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

interface IngestMethodData {
  method: string;
  count: number;
  pct: number;
}

interface Props {
  data: IngestMethodData[];
}

// Color palette for ingest methods
const METHOD_COLORS: Record<string, string> = {
  url: '#0f766e',      // teal - web crawls
  file: '#f59e0b',     // amber - file uploads
  text: '#6366f1',     // indigo - text paste
  directory: '#8b5cf6', // violet - directory import
};

const METHOD_LABELS: Record<string, string> = {
  url: 'URL Crawl',
  file: 'File Upload',
  text: 'Text Paste',
  directory: 'Directory',
};

export function IngestMethodChart({ data }: Props) {
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
        No data available
      </div>
    );
  }

  // Transform data for chart
  const chartData = data.map((d) => ({
    name: METHOD_LABELS[d.method] || d.method,
    value: d.count,
    pct: d.pct,
    color: METHOD_COLORS[d.method] || '#6b7280',
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={80}
          paddingAngle={2}
          dataKey="value"
          label={({ cx, cy, midAngle = 0, outerRadius, name, payload }) => {
            const RADIAN = Math.PI / 180;
            const radius = (outerRadius || 80) + 25;
            const x = (cx || 0) + radius * Math.cos(-midAngle * RADIAN);
            const y = (cy || 0) + radius * Math.sin(-midAngle * RADIAN);
            return (
              <text
                x={x}
                y={y}
                fill="var(--cream)"
                textAnchor={x > cx ? 'start' : 'end'}
                dominantBaseline="central"
                fontSize={12}
              >
                {`${name}: ${payload.pct}%`}
              </text>
            );
          }}
          labelLine={false}
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--charcoal)',
            border: '1px solid var(--charcoal-lighter)',
            borderRadius: 8,
          }}
          itemStyle={{ color: 'var(--cream)' }}
          labelStyle={{ color: 'var(--cream)' }}
          formatter={(value, _name, props) => {
            const item = props.payload;
            return [`${value} ingests (${item.pct}%)`, item.name];
          }}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          formatter={(value) => (
            <span style={{ color: 'var(--cream)', fontSize: 12 }}>{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
