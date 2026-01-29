/**
 * CollectionQualityChart - Bar chart comparing quality scores across collections
 */

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface CollectionQuality {
  collection: string;
  avg: number | null;
  min: number | null;
  max: number | null;
  doc_count: number;
}

interface Props {
  data: CollectionQuality[];
}

export function CollectionQualityChart({ data }: Props) {
  // If no data, show placeholder
  if (data.length === 0) {
    return (
      <div
        style={{
          height: 300,
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

  // Transform data for chart - convert nulls to 0 and scale to percentage
  const chartData = data.map((d) => ({
    collection: d.collection.length > 20 ? d.collection.slice(0, 18) + '...' : d.collection,
    fullName: d.collection,
    avg: d.avg !== null ? Math.round(d.avg * 100) : 0,
    min: d.min !== null ? Math.round(d.min * 100) : 0,
    max: d.max !== null ? Math.round(d.max * 100) : 0,
    doc_count: d.doc_count,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 10, right: 30, left: 100, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="var(--charcoal-lighter)" horizontal={false} />
        <XAxis
          type="number"
          domain={[0, 100]}
          stroke="var(--warm-gray)"
          fontSize={12}
          tickLine={false}
          tickFormatter={(value) => `${value}%`}
        />
        <YAxis
          type="category"
          dataKey="collection"
          stroke="var(--warm-gray)"
          fontSize={12}
          tickLine={false}
          width={90}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--charcoal)',
            border: '1px solid var(--charcoal-lighter)',
            borderRadius: 8,
            color: 'var(--cream)',
          }}
          labelFormatter={(label, payload) => {
            const item = payload?.[0]?.payload;
            return item?.fullName || label;
          }}
          formatter={(value, name, props) => {
            const item = props.payload;
            if (name === 'avg') {
              return [
                `${value}% avg (${item.doc_count} docs)`,
                'Quality',
              ];
            }
            return [`${value}%`, name as string];
          }}
        />
        <Bar
          dataKey="avg"
          fill="#f59e0b"
          radius={[0, 4, 4, 0]}
          maxBarSize={30}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
