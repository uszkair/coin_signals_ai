import React from 'react';
import { FaArrowUp, FaArrowDown, FaTimes, FaChartLine } from 'react-icons/fa';
import CandlestickPatternVisualizer from './CandlestickPatternVisualizer';

/**
 * Modal component to display detailed signal information
 * @param {Object} props - Component props
 * @param {Object} props.signal - Signal object to display
 * @param {boolean} props.isOpen - Whether the modal is open
 * @param {Function} props.onClose - Function to call when the modal is closed
 * @param {Function} props.onViewChart - Function to call when the "View on Chart" button is clicked
 */
const SignalDetailsModal = ({ signal, isOpen, onClose, onViewChart }) => {
  if (!isOpen || !signal) {
    return null;
  }

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch (e) {
      return timestamp;
    }
  };

  // Format duration
  const formatDuration = (minutes) => {
    if (!minutes && minutes !== 0) return 'N/A';
    
    if (minutes < 60) {
      return `${minutes} minutes`;
    } else if (minutes < 1440) {
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      return `${hours} hours, ${mins} minutes`;
    } else {
      const days = Math.floor(minutes / 1440);
      const hours = Math.floor((minutes % 1440) / 60);
      return `${days} days, ${hours} hours`;
    }
  };

  // Get signal icon and color
  const getSignalDisplay = () => {
    switch (signal.signal) {
      case 'BUY':
        return {
          icon: <FaArrowUp className="text-xl" />,
          color: 'bg-success text-white'
        };
      case 'SELL':
        return {
          icon: <FaArrowDown className="text-xl" />,
          color: 'bg-danger text-white'
        };
      default:
        return {
          icon: null,
          color: 'bg-warning text-white'
        };
    }
  };

  // Get outcome text and class
  const getOutcomeDisplay = () => {
    switch (signal.outcome) {
      case 'take_profit_hit':
        return {
          text: 'Take Profit Hit',
          class: 'text-success'
        };
      case 'stop_loss_hit':
        return {
          text: 'Stop Loss Hit',
          class: 'text-danger'
        };
      case 'undecided':
        return {
          text: 'Pending',
          class: 'text-gray-500 dark:text-gray-400'
        };
      default:
        return {
          text: signal.outcome || 'N/A',
          class: 'text-gray-500 dark:text-gray-400'
        };
    }
  };

  const signalDisplay = getSignalDisplay();
  const outcomeDisplay = getOutcomeDisplay();

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75 dark:bg-gray-900 dark:bg-opacity-75" 
          onClick={onClose}
        ></div>
        
        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          {/* Header */}
          <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full ${signalDisplay.color} mr-3`}>
                {signalDisplay.icon}
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                {signal.signal} Signal Details
              </h3>
            </div>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
            >
              <FaTimes />
            </button>
          </div>
          
          {/* Content */}
          <div className="px-6 py-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left column */}
              <div>
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Timestamp</h4>
                  <p className="text-base font-medium">{formatTimestamp(signal.timestamp)}</p>
                </div>
                
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Pattern</h4>
                  <p className="text-base font-medium">{signal.pattern}</p>
                </div>
                
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Entry Price</h4>
                  <p className="text-base font-medium">{signal.entry?.toFixed(2) || 'N/A'}</p>
                </div>
                
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Stop Loss</h4>
                  <p className="text-base font-medium text-danger">{signal.stop_loss?.toFixed(2) || 'N/A'}</p>
                </div>
                
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Take Profit</h4>
                  <p className="text-base font-medium text-success">{signal.take_profit?.toFixed(2) || 'N/A'}</p>
                </div>
                
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Risk/Reward Ratio</h4>
                  <p className="text-base font-medium">1:{signal.rr_ratio || 'N/A'}</p>
                </div>
              </div>
              
              {/* Right column */}
              <div>
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Trend</h4>
                  <p className="text-base font-medium">
                    {signal.trend === 'BUY' ? (
                      <span className="text-success">Bullish</span>
                    ) : signal.trend === 'SELL' ? (
                      <span className="text-danger">Bearish</span>
                    ) : (
                      <span className="text-warning">Sideways</span>
                    )}
                  </p>
                </div>
                
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Confidence Score</h4>
                  <div className="flex items-center">
                    <span className="text-base font-medium mr-2">{signal.score}/4</span>
                    <div className="flex">
                      {[...Array(4)].map((_, i) => (
                        <div 
                          key={i} 
                          className={`w-2 h-2 rounded-full mx-0.5 ${
                            i < (signal.score || 0) 
                              ? 'bg-primary' 
                              : 'bg-gray-300 dark:bg-gray-600'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Outcome</h4>
                  <p className={`text-base font-medium ${outcomeDisplay.class}`}>
                    {outcomeDisplay.text}
                  </p>
                </div>
                
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Duration</h4>
                  <p className="text-base font-medium">{formatDuration(signal.duration_minutes)}</p>
                </div>
                
                {signal.exit_timestamp && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Exit Time</h4>
                    <p className="text-base font-medium">{formatTimestamp(signal.exit_timestamp)}</p>
                  </div>
                )}
                
                {signal.exit_price && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Exit Price</h4>
                    <p className="text-base font-medium">{signal.exit_price.toFixed(2)}</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* Pattern visualization */}
            {signal.pattern && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Pattern Visualization</h4>
                <CandlestickPatternVisualizer 
                  pattern={{ 
                    name: signal.pattern, 
                    direction: signal.signal === 'BUY' ? 'bullish' : signal.signal === 'SELL' ? 'bearish' : 'neutral',
                    confidence: signal.score
                  }} 
                />
              </div>
            )}
            
            {/* Comment */}
            {signal.comment && (
              <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Analysis</h4>
                <p className="text-sm">{signal.comment}</p>
              </div>
            )}
          </div>
          
          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-between">
            <button
              onClick={onClose}
              className="btn btn-secondary"
            >
              Close
            </button>
            
            <button
              onClick={() => onViewChart(signal)}
              className="btn btn-primary flex items-center"
            >
              <FaChartLine className="mr-2" />
              View on Chart
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignalDetailsModal;