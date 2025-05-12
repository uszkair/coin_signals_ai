import React from 'react';
import { FaArrowUp, FaArrowDown, FaMinus, FaInfoCircle } from 'react-icons/fa';

/**
 * Component to display signal history in a table format
 * @param {Object} props - Component props
 * @param {Array} props.signals - Array of signal objects
 * @param {Function} props.onRowClick - Function to call when a row is clicked
 */
const SignalTable = ({ signals, onRowClick }) => {
  if (!signals || signals.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
        <p className="text-gray-500 dark:text-gray-400">No signals found for the selected criteria.</p>
      </div>
    );
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
      return `${minutes} min`;
    } else if (minutes < 1440) {
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      return `${hours}h ${mins}m`;
    } else {
      const days = Math.floor(minutes / 1440);
      const hours = Math.floor((minutes % 1440) / 60);
      return `${days}d ${hours}h`;
    }
  };

  // Get row class based on outcome
  const getRowClass = (outcome) => {
    switch (outcome) {
      case 'take_profit_hit':
        return 'bg-green-50 dark:bg-green-900 dark:bg-opacity-20 hover:bg-green-100 dark:hover:bg-green-900 dark:hover:bg-opacity-30';
      case 'stop_loss_hit':
        return 'bg-red-50 dark:bg-red-900 dark:bg-opacity-20 hover:bg-red-100 dark:hover:bg-red-900 dark:hover:bg-opacity-30';
      default:
        return 'hover:bg-gray-50 dark:hover:bg-gray-700';
    }
  };

  // Get signal icon
  const getSignalIcon = (signal) => {
    switch (signal) {
      case 'BUY':
        return <FaArrowUp className="text-success" />;
      case 'SELL':
        return <FaArrowDown className="text-danger" />;
      default:
        return <FaMinus className="text-warning" />;
    }
  };

  // Get outcome text and class
  const getOutcomeDisplay = (outcome) => {
    switch (outcome) {
      case 'take_profit_hit':
        return {
          text: 'TP Hit',
          class: 'text-success'
        };
      case 'stop_loss_hit':
        return {
          text: 'SL Hit',
          class: 'text-danger'
        };
      case 'undecided':
        return {
          text: 'Pending',
          class: 'text-gray-500 dark:text-gray-400'
        };
      default:
        return {
          text: outcome || 'N/A',
          class: 'text-gray-500 dark:text-gray-400'
        };
    }
  };

  // Render confidence score dots
  const renderScoreDots = (score) => {
    return (
      <div className="flex">
        {[...Array(4)].map((_, i) => (
          <div 
            key={i} 
            className={`w-2 h-2 rounded-full mx-0.5 ${
              i < (score || 0) 
                ? 'bg-primary' 
                : 'bg-gray-300 dark:bg-gray-600'
            }`}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Time
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Signal
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Pattern
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Entry
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              SL / TP
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Score
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Outcome
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Duration
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Details
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          {signals.map((signal, index) => {
            const outcomeDisplay = getOutcomeDisplay(signal.outcome);
            
            return (
              <tr 
                key={index} 
                className={getRowClass(signal.outcome)}
                onClick={() => onRowClick(signal)}
              >
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  {formatTimestamp(signal.timestamp)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center">
                    {getSignalIcon(signal.signal)}
                    <span className="ml-2">{signal.signal}</span>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  {signal.pattern}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  {signal.entry?.toFixed(2) || 'N/A'}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  <div className="text-danger">{signal.stop_loss?.toFixed(2) || 'N/A'}</div>
                  <div className="text-success">{signal.take_profit?.toFixed(2) || 'N/A'}</div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  {renderScoreDots(signal.score)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  <span className={outcomeDisplay.class}>
                    {outcomeDisplay.text}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  {formatDuration(signal.duration_minutes)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  <button 
                    className="text-primary hover:text-primary-dark"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRowClick(signal);
                    }}
                  >
                    <FaInfoCircle />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default SignalTable;