import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

/**
 * Custom hook to fetch and manage signal history data
 * @param {Object} options - Configuration options
 * @param {string} options.symbol - Trading pair symbol (e.g., "BTCUSDT")
 * @param {string} options.interval - Timeframe (e.g., "1h", "4h")
 * @param {number} options.days - Number of days to look back (default: 30)
 * @param {Object} options.filters - Optional filters for the data
 * @returns {Object} - { data, loading, error, refetch, applyFilters }
 */
const useSignalHistory = ({ symbol, interval, days = 30, filters = {} }) => {
  const [data, setData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Calculate the date range for the API request
  const getDateRange = useCallback(() => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    
    return {
      year: startDate.getFullYear(),
      month: startDate.getMonth() + 1, // JavaScript months are 0-indexed
    };
  }, [days]);

  // Fetch data from the API
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get date range for API request
      const { year, month } = getDateRange();
      
      // Fetch data from the backtest API
      const response = await axios.get('/api/backtest', {
        params: {
          symbol,
          interval,
          lookback_days: days,
          risk_reward_ratio: 1.5 // Default risk-reward ratio
        }
      });
      
      if (response.data && response.data.signals) {
        // Sort signals by timestamp (newest first)
        const sortedData = response.data.signals.sort((a, b) => {
          return new Date(b.timestamp) - new Date(a.timestamp);
        });
        
        setData(sortedData);
        applyFilters(sortedData, filters);
      } else {
        setData([]);
        setFilteredData([]);
      }
    } catch (err) {
      console.error('Error fetching signal history:', err);
      setError('Failed to load signal history. Please try again later.');
      setData([]);
      setFilteredData([]);
    } finally {
      setLoading(false);
    }
  }, [symbol, interval, days, getDateRange]);

  // Apply filters to the data
  const applyFilters = useCallback((dataToFilter = data, newFilters = filters) => {
    let filtered = [...dataToFilter];
    
    // Filter by signal type
    if (newFilters.signalType && newFilters.signalType !== 'all') {
      filtered = filtered.filter(item => item.signal === newFilters.signalType);
    }
    
    // Filter by minimum score
    if (newFilters.minScore !== undefined && newFilters.minScore > 0) {
      filtered = filtered.filter(item => item.score >= newFilters.minScore);
    }
    
    // Filter by outcome
    if (newFilters.outcome && newFilters.outcome !== 'all') {
      filtered = filtered.filter(item => item.outcome === newFilters.outcome);
    }
    
    // Filter by pattern
    if (newFilters.pattern && newFilters.pattern !== 'all') {
      filtered = filtered.filter(item => item.pattern === newFilters.pattern);
    }
    
    setFilteredData(filtered);
  }, [data, filters]);

  // Fetch data when dependencies change
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Apply filters when filters change
  useEffect(() => {
    applyFilters();
  }, [filters, applyFilters]);

  return {
    data: filteredData,
    rawData: data,
    loading,
    error,
    refetch: fetchData,
    applyFilters
  };
};

export default useSignalHistory;