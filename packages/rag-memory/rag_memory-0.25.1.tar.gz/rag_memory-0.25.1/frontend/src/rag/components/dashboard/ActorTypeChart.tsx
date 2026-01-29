/**
 * ActorTypeChart - Horizontal bar chart showing who is ingesting content
 */

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface ActorTypeData {
  actor: string;
  count: number;
  pct: number;
}

interface Props {
  data: ActorTypeData[];
}

// Color palette for actor types
const ACTOR_COLORS: Record<string, string> = {
  agent: '#0f766e',  // teal - AI agents
  user: '#f59e0b',   // amber - human users
  api: '#6366f1',    // indigo - API/scripts
};

const ACTOR_LABELS: Record<string, string> = {
  agent: 'AI Agent',
  user: 'Human User',
  api: 'API/Script',
};

export function ActorTypeChart({ data }: Props) {
  // If no data, show placeholder
  if (data.length === 0) {
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
        No data available
      </div>
    );
  }

  // Transform data for chart
  const chartData = data.map((d) => ({
    name: ACTOR_LABELS[d.actor] || d.actor,
    count: d.count,
    pct: d.pct,
    fill: ACTOR_COLORS[d.actor] || '#6b7280',
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 10, right: 30, left: 80, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="var(--charcoal-lighter)" horizontal={false} />
        <XAxis
          type="number"
          stroke="var(--warm-gray)"
          fontSize={12}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="name"
          stroke="var(--warm-gray)"
          fontSize={12}
          tickLine={false}
          width={75}
        />
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
            return [`${value} ingests (${item.pct}%)`, 'Count'];
          }}
        />
        <Bar
          dataKey="count"
          radius={[0, 4, 4, 0]}
          maxBarSize={30}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
