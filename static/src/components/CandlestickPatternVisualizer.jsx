import React from 'react';

/**
 * Component to visualize candlestick patterns
 * @param {Object} pattern - The pattern object from the API
 */
const CandlestickPatternVisualizer = ({ pattern }) => {
  if (!pattern || !pattern.name) {
    return null;
  }

  // Render different visualizations based on pattern type
  const renderPatternVisualization = () => {
    switch (pattern.name) {
      case 'Doji':
        return renderDoji();
      case 'Hammer':
        return renderHammer();
      case 'Inverted Hammer':
        return renderInvertedHammer();
      case 'Shooting Star':
        return renderShootingStar();
      case 'Bullish Engulfing':
        return renderBullishEngulfing();
      case 'Bearish Engulfing':
        return renderBearishEngulfing();
      default:
        return renderGenericPattern();
    }
  };

  // Render a Doji pattern
  const renderDoji = () => (
    <div className="flex items-center justify-center h-24">
      <div className="flex flex-col items-center">
        <div className="w-0.5 h-6 bg-gray-500"></div>
        <div className="w-4 h-0.5 bg-gray-700"></div>
        <div className="w-0.5 h-6 bg-gray-500"></div>
        <div className="mt-2 text-xs text-center">Doji</div>
      </div>
    </div>
  );

  // Render a Hammer pattern
  const renderHammer = () => (
    <div className="flex items-center justify-center h-24">
      <div className="flex flex-col items-center">
        <div className="w-0.5 h-1 bg-gray-500"></div>
        <div className="w-4 h-2 bg-green-500"></div>
        <div className="w-0.5 h-10 bg-gray-500"></div>
        <div className="mt-2 text-xs text-center">Hammer</div>
      </div>
    </div>
  );

  // Render an Inverted Hammer pattern
  const renderInvertedHammer = () => (
    <div className="flex items-center justify-center h-24">
      <div className="flex flex-col items-center">
        <div className="w-0.5 h-10 bg-gray-500"></div>
        <div className="w-4 h-2 bg-green-500"></div>
        <div className="w-0.5 h-1 bg-gray-500"></div>
        <div className="mt-2 text-xs text-center">Inverted Hammer</div>
      </div>
    </div>
  );

  // Render a Shooting Star pattern
  const renderShootingStar = () => (
    <div className="flex items-center justify-center h-24">
      <div className="flex flex-col items-center">
        <div className="w-0.5 h-10 bg-gray-500"></div>
        <div className="w-4 h-2 bg-red-500"></div>
        <div className="w-0.5 h-1 bg-gray-500"></div>
        <div className="mt-2 text-xs text-center">Shooting Star</div>
      </div>
    </div>
  );

  // Render a Bullish Engulfing pattern
  const renderBullishEngulfing = () => (
    <div className="flex items-center justify-center h-24">
      <div className="flex items-end space-x-1">
        <div className="flex flex-col items-center">
          <div className="w-0.5 h-2 bg-gray-500"></div>
          <div className="w-3 h-4 bg-red-500"></div>
          <div className="w-0.5 h-2 bg-gray-500"></div>
        </div>
        <div className="flex flex-col items-center">
          <div className="w-0.5 h-2 bg-gray-500"></div>
          <div className="w-5 h-6 bg-green-500"></div>
          <div className="w-0.5 h-2 bg-gray-500"></div>
        </div>
      </div>
      <div className="ml-2 text-xs">Bullish Engulfing</div>
    </div>
  );

  // Render a Bearish Engulfing pattern
  const renderBearishEngulfing = () => (
    <div className="flex items-center justify-center h-24">
      <div className="flex items-end space-x-1">
        <div className="flex flex-col items-center">
          <div className="w-0.5 h-2 bg-gray-500"></div>
          <div className="w-3 h-4 bg-green-500"></div>
          <div className="w-0.5 h-2 bg-gray-500"></div>
        </div>
        <div className="flex flex-col items-center">
          <div className="w-0.5 h-2 bg-gray-500"></div>
          <div className="w-5 h-6 bg-red-500"></div>
          <div className="w-0.5 h-2 bg-gray-500"></div>
        </div>
      </div>
      <div className="ml-2 text-xs">Bearish Engulfing</div>
    </div>
  );

  // Render a generic pattern
  const renderGenericPattern = () => (
    <div className="flex items-center justify-center h-24">
      <div className="text-center">
        <div className="text-sm font-medium">{pattern.name}</div>
        <div className="text-xs capitalize">{pattern.direction}</div>
      </div>
    </div>
  );

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-md">
      <h3 className="text-lg font-bold mb-2 text-center">Pattern Visualization</h3>
      <div className="flex justify-center">
        <div className={`px-3 py-1 rounded text-xs font-medium ${
          pattern.direction === 'bullish' ? 'bg-success bg-opacity-10 text-success' : 
          pattern.direction === 'bearish' ? 'bg-danger bg-opacity-10 text-danger' : 
          'bg-gray-200 dark:bg-gray-700'
        }`}>
          {pattern.direction.toUpperCase()}
        </div>
      </div>
      {renderPatternVisualization()}
      <div className="mt-2 flex justify-center">
        <div className="flex items-center">
          <span className="text-xs mr-2">Confidence:</span>
          <div className="flex">
            {[...Array(4)].map((_, i) => (
              <div 
                key={i} 
                className={`w-2 h-2 rounded-full mx-0.5 ${
                  i < (pattern.confidence || 0) 
                    ? 'bg-primary' 
                    : 'bg-gray-300 dark:bg-gray-600'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CandlestickPatternVisualizer;