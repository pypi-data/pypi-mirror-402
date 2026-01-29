/**
 * FileTypeChart - Donut chart showing file type distribution
 */

import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

interface FileTypeData {
  type: string;
  count: number;
  size_bytes: number;
  pct: number;
}

interface Props {
  data: FileTypeData[];
}

// Color palette for file types
const COLORS = [
  '#f59e0b', // amber
  '#0f766e', // teal
  '#6366f1', // indigo
  '#ec4899', // pink
  '#8b5cf6', // violet
  '#14b8a6', // teal-light
  '#f97316', // orange
  '#06b6d4', // cyan
];

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export function FileTypeChart({ data }: Props) {
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

  // Transform data for chart - use type as name
  const chartData = data.map((d, i) => ({
    name: d.type.toUpperCase(),
    value: d.count,
    size_bytes: d.size_bytes,
    pct: d.pct,
    color: COLORS[i % COLORS.length],
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
            return [
              `${value} docs (${formatBytes(item.size_bytes)})`,
              item.name,
            ];
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
