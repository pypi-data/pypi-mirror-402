/**
 * ReviewStatusChart - Pie chart showing reviewed vs unreviewed documents
 */

import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

interface Props {
  data: { reviewed: number; unreviewed: number };
}

const COLORS = {
  reviewed: '#10b981',    // emerald for reviewed
  unreviewed: '#6b7280',  // gray for unreviewed
};

export function ReviewStatusChart({ data }: Props) {
  const chartData = [
    { name: 'Reviewed', value: data.reviewed, color: COLORS.reviewed },
    { name: 'Unreviewed', value: data.unreviewed, color: COLORS.unreviewed },
  ];

  const total = data.reviewed + data.unreviewed;

  // If no data, show placeholder
  if (total === 0) {
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
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="45%"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={2}
          dataKey="value"
          label={false}
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
          formatter={(value, name) => [
            `${value} documents (${(((value as number) / total) * 100).toFixed(1)}%)`,
            name as string,
          ]}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          formatter={(value) => (
            <span style={{ color: 'var(--cream)' }}>{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
