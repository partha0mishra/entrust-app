/**
 * Metrics table component for displaying aggregated data
 * Shows facet names with their statistical metrics
 *
 * @param {Array} data - Array of objects with metrics (name, avg_score, min_score, max_score, count, etc.)
 * @param {string} facetType - Type of facet being displayed
 */
export default function MetricsTable({ data, facetType = 'Item' }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 text-gray-500 border border-gray-200 rounded-lg">
        No metrics data available
      </div>
    );
  }

  // Sort by average score descending
  const sortedData = [...data].sort((a, b) => (b.avg_score || 0) - (a.avg_score || 0));

  // Color coding for scores
  const getScoreColor = (score) => {
    if (!score) return 'text-gray-400';
    if (score >= 8) return 'text-green-600 font-semibold';
    if (score >= 6) return 'text-blue-600 font-semibold';
    if (score >= 4) return 'text-orange-600 font-semibold';
    return 'text-red-600 font-semibold';
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
              {facetType}
            </th>
            <th className="px-6 py-3 text-center text-xs font-medium text-gray-700 uppercase tracking-wider">
              Avg Score
            </th>
            <th className="px-6 py-3 text-center text-xs font-medium text-gray-700 uppercase tracking-wider">
              Min
            </th>
            <th className="px-6 py-3 text-center text-xs font-medium text-gray-700 uppercase tracking-wider">
              Max
            </th>
            <th className="px-6 py-3 text-center text-xs font-medium text-gray-700 uppercase tracking-wider">
              Responses
            </th>
            <th className="px-6 py-3 text-center text-xs font-medium text-gray-700 uppercase tracking-wider">
              Respondents
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedData.map((row, index) => (
            <tr key={index} className="hover:bg-gray-50 transition-colors">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {row.name}
              </td>
              <td className={`px-6 py-4 whitespace-nowrap text-sm text-center ${getScoreColor(row.avg_score)}`}>
                {row.avg_score ? row.avg_score.toFixed(2) : 'N/A'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-center">
                {row.min_score ? row.min_score.toFixed(2) : 'N/A'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-center">
                {row.max_score ? row.max_score.toFixed(2) : 'N/A'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-center">
                {row.count || 0}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-center">
                {row.respondents || 0}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-3 text-xs text-gray-500 px-2">
        <strong>Note:</strong> Scores are on a scale of 1-10. Color coding:
        <span className="ml-2 text-green-600 font-semibold">Green (8-10)</span>,
        <span className="ml-2 text-blue-600 font-semibold">Blue (6-7.9)</span>,
        <span className="ml-2 text-orange-600 font-semibold">Orange (4-5.9)</span>,
        <span className="ml-2 text-red-600 font-semibold">Red (&lt;4)</span>
      </div>
    </div>
  );
}
