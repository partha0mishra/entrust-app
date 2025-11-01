import ReactWordcloud from 'react-wordcloud';

/**
 * Word cloud component for visualizing comment frequency
 * Shows the most frequently mentioned words from survey comments
 *
 * @param {Object} wordFrequency - Object mapping words to their frequency counts
 * @param {string} title - Chart title
 */
export default function CommentWordCloud({ wordFrequency, title }) {
  if (!wordFrequency || Object.keys(wordFrequency).length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 border border-gray-200 rounded-lg">
        No comment data available for word cloud
      </div>
    );
  }

  // Convert frequency object to word cloud format
  const words = Object.entries(wordFrequency).map(([text, value]) => ({
    text,
    value
  }));

  const options = {
    colors: ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899'],
    enableTooltip: true,
    deterministic: true,
    fontFamily: 'system-ui, -apple-system, sans-serif',
    fontSizes: [16, 60],
    fontStyle: 'normal',
    fontWeight: 'normal',
    padding: 2,
    rotations: 2,
    rotationAngles: [0, 90],
    scale: 'sqrt',
    spiral: 'archimedean',
    transitionDuration: 1000
  };

  const callbacks = {
    getWordTooltip: (word) => `${word.text}: mentioned ${word.value} time${word.value > 1 ? 's' : ''}`,
  };

  return (
    <div>
      {title && <h4 className="text-sm font-medium text-gray-700 mb-2">{title}</h4>}
      <div className="border border-gray-200 rounded-lg p-4 bg-white" style={{ height: 400 }}>
        <ReactWordcloud
          words={words}
          options={options}
          callbacks={callbacks}
        />
      </div>
      <div className="mt-3 text-xs text-gray-600 px-2">
        <strong>Word Cloud:</strong> Larger words appear more frequently in survey comments.
        Hover over words to see exact counts.
      </div>
    </div>
  );
}
