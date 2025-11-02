import { useMemo, useState } from 'react';
import { Wordcloud } from '@visx/wordcloud';
import { scaleLog } from '@visx/scale';
import { Text } from '@visx/text';

/**
 * Word cloud component for visualizing comment frequency
 * Shows the most frequently mentioned words from survey comments
 *
 * @param {Object} wordFrequency - Object mapping words to their frequency counts
 * @param {string} title - Chart title
 */
export default function CommentWordCloud({ wordFrequency, title }) {
  const [hoveredWord, setHoveredWord] = useState(null);

  const words = useMemo(() => {
    if (!wordFrequency || Object.keys(wordFrequency).length === 0) {
      return [];
    }

    // Convert frequency object to word cloud format
    return Object.entries(wordFrequency).map(([text, value]) => ({
      text,
      value
    }));
  }, [wordFrequency]);

  if (words.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 border border-gray-200 rounded-lg">
        No comment data available for word cloud
      </div>
    );
  }

  // Color palette
  const colors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899'];

  // Font size scale based on word frequency
  const fontScale = scaleLog({
    domain: [Math.min(...words.map(w => w.value)), Math.max(...words.map(w => w.value))],
    range: [14, 72],
  });

  const fontSizeSetter = (datum) => fontScale(datum.value);

  // Fixed dimensions for the word cloud
  const width = 800;
  const height = 400;

  return (
    <div>
      {title && <h4 className="text-sm font-medium text-gray-700 mb-2">{title}</h4>}
      <div className="border border-gray-200 rounded-lg p-4 bg-white overflow-hidden">
        <div className="flex items-center justify-center" style={{ width: '100%', height: 400 }}>
          <svg width={width} height={height}>
            <rect width={width} height={height} fill="white" />
            <Wordcloud
              words={words}
              width={width}
              height={height}
              fontSize={fontSizeSetter}
              font="system-ui, -apple-system, sans-serif"
              padding={2}
              spiral="archimedean"
              rotate={0}
              random={() => 0.5}
            >
              {(cloudWords) =>
                cloudWords.map((w, i) => (
                  <Text
                    key={w.text}
                    fill={colors[i % colors.length]}
                    textAnchor="middle"
                    transform={`translate(${w.x}, ${w.y}) rotate(${w.rotate})`}
                    fontSize={w.size}
                    fontFamily={w.font}
                    onMouseEnter={() => setHoveredWord(w)}
                    onMouseLeave={() => setHoveredWord(null)}
                    style={{
                      cursor: 'pointer',
                      transition: 'opacity 0.2s',
                      opacity: hoveredWord && hoveredWord.text !== w.text ? 0.5 : 1
                    }}
                  >
                    {w.text}
                  </Text>
                ))
              }
            </Wordcloud>
          </svg>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredWord && (
        <div className="mt-2 p-3 bg-gray-100 rounded-lg border border-gray-300">
          <p className="text-sm font-medium text-gray-900">
            "{hoveredWord.text}": mentioned {hoveredWord.value} time{hoveredWord.value > 1 ? 's' : ''}
          </p>
        </div>
      )}

      <div className="mt-3 text-xs text-gray-600 px-2">
        <strong>Word Cloud:</strong> Larger words appear more frequently in survey comments.
        Hover over words to see exact counts.
      </div>
    </div>
  );
}
