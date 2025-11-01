import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';

/**
 * RadarChart component for multi-dimensional scoring visualization
 * Shows relative performance across multiple dimensions or facets
 *
 * @param {Array} data - Array of objects with 'name' and 'score' properties
 * @param {string} title - Chart title
 */
export default function DimensionRadarChart({ data, title }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No data available for radar chart
      </div>
    );
  }

  return (
    <div>
      {title && <h4 className="text-sm font-medium text-gray-700 mb-2">{title}</h4>}
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={data}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis
            dataKey="name"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickLine={false}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 10]}
            tick={{ fill: '#9ca3af', fontSize: 10 }}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke="#10b981"
            fill="#10b981"
            fillOpacity={0.6}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              padding: '8px'
            }}
          />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
