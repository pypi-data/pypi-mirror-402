/**
 * QualityHistogram - Bar chart showing quality score distribution
 */

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface Props {
  data: Array<{ range: string; count: number }>;
  color?: string;
}

export function QualityHistogram({ data, color = '#f59e0b' }: Props) {
  // If all counts are 0, show a placeholder
  const hasData = data.some((d) => d.count > 0);

  if (!hasData) {
    return (
      <div
        style={{
          height: 250,
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

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--charcoal-lighter)" />
        <XAxis
          dataKey="range"
          stroke="var(--warm-gray)"
          fontSize={12}
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
            color: 'var(--cream)',
          }}
          labelStyle={{ color: 'var(--cream)', fontWeight: 600 }}
          formatter={(value) => [`${value} documents`, 'Count']}
        />
        <Bar
          dataKey="count"
          fill={color}
          radius={[4, 4, 0, 0]}
          maxBarSize={60}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
