import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

/**
 * Bar chart component for facet-level comparisons
 * Shows scores across categories, processes, or lifecycle stages
 *
 * @param {Array} data - Array of objects with 'name', 'avg_score', and optionally 'count'
 * @param {string} facetType - Type of facet ('category', 'process', or 'lifecycle_stage')
 * @param {string} title - Chart title
 */
export default function FacetBarChart({ data, facetType = 'category', title }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No data available for {facetType} analysis
      </div>
    );
  }

  // Color scheme based on score
  const getBarColor = (score) => {
    if (score >= 8) return '#10b981'; // Green - excellent
    if (score >= 6) return '#3b82f6'; // Blue - good
    if (score >= 4) return '#f59e0b'; // Orange - needs improvement
    return '#ef4444'; // Red - critical
  };

  // Sort data by score descending
  const sortedData = [...data].sort((a, b) => (b.avg_score || 0) - (a.avg_score || 0));

  return (
    <div>
      {title && <h4 className="text-sm font-medium text-gray-700 mb-2">{title}</h4>}
      <ResponsiveContainer width="100%" height={450}>
        <BarChart
          data={sortedData}
          margin={{ top: 30, right: 30, left: 40, bottom: 100 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={100}
            tick={{ fill: '#6b7280', fontSize: 11 }}
            interval={0}
          />
          <YAxis
            domain={[0, 10]}
            tick={{ fill: '#6b7280', fontSize: 12 }}
            label={{ value: 'Average Score', angle: -90, position: 'insideLeft', style: { fill: '#6b7280' } }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              padding: '8px'
            }}
            formatter={(value, name) => {
              if (name === 'avg_score') return [value.toFixed(2), 'Avg Score'];
              if (name === 'count') return [value, 'Responses'];
              return [value, name];
            }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            formatter={(value) => {
              if (value === 'avg_score') return 'Average Score';
              if (value === 'count') return 'Response Count';
              return value;
            }}
          />
          <Bar dataKey="avg_score" radius={[8, 8, 0, 0]}>
            {sortedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.avg_score)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-700">
          <strong>Legend:</strong>
          <span className="ml-2">
            <span className="inline-block w-3 h-3 bg-green-500 rounded mr-1"></span>
            Excellent (8-10)
          </span>
          <span className="ml-3">
            <span className="inline-block w-3 h-3 bg-blue-500 rounded mr-1"></span>
            Good (6-7.9)
          </span>
          <span className="ml-3">
            <span className="inline-block w-3 h-3 bg-orange-500 rounded mr-1"></span>
            Needs Improvement (4-5.9)
          </span>
          <span className="ml-3">
            <span className="inline-block w-3 h-3 bg-red-500 rounded mr-1"></span>
            Critical (&lt;4)
          </span>
        </p>
      </div>
    </div>
  );
}
