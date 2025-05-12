import { useState, useEffect } from 'react'
import axios from 'axios'

// Base API URL
const API_BASE_URL = '/api'

/**
 * Custom hook for fetching data from the API
 * @param {string} endpoint - API endpoint to fetch data from
 * @param {Object} params - Query parameters
 * @param {boolean} autoFetch - Whether to fetch data automatically on mount
 * @returns {Object} - { data, loading, error, refetch }
 */
export const useApi = (endpoint, params = {}, autoFetch = true) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(autoFetch)
  const [error, setError] = useState(null)

  const fetchData = async (customParams = {}) => {
    try {
      setLoading(true)
      setError(null)
      
      const mergedParams = { ...params, ...customParams }
      const response = await axios.get(`${API_BASE_URL}${endpoint}`, { params: mergedParams })
      
      setData(response.data)
      return response.data
    } catch (err) {
      setError(err.message || 'An error occurred')
      return null
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (autoFetch) {
      fetchData()
    }
  }, [endpoint, JSON.stringify(params)])

  return { data, loading, error, refetch: fetchData }
}

/**
 * Get trading signal for a specific symbol and timeframe
 * @param {string} symbol - Cryptocurrency symbol (e.g., BTCUSDT)
 * @param {string} interval - Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
 * @param {string} mode - Trading mode (scalp, swing)
 * @returns {Object} - { data, loading, error, refetch }
 */
export const useSignal = (symbol, interval = '1h', mode = 'swing') => {
  return useApi(`/signal/${symbol}`, { interval, mode })
}

/**
 * Get multi-timeframe trading signal for a specific symbol
 * @param {string} symbol - Cryptocurrency symbol (e.g., BTCUSDT)
 * @param {string} mode - Trading mode (scalp, swing)
 * @returns {Object} - { data, loading, error, refetch }
 */
export const useSignalMTF = (symbol, mode = 'swing') => {
  return useApi(`/signal-mtf/${symbol}`, { mode })
}

/**
 * Get trading signals for multiple symbols
 * @param {Array} symbols - List of cryptocurrency symbols
 * @param {string} interval - Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
 * @param {string} mode - Trading mode (scalp, swing)
 * @returns {Object} - { data, loading, error, refetch }
 */
export const useSignals = (symbols = null, interval = '1h', mode = 'swing') => {
  const params = { interval, mode }
  
  // Handle multiple symbols
  if (symbols && symbols.length > 0) {
    // If only one symbol, use the single symbol endpoint for better data
    if (symbols.length === 1) {
      return useApi(`/signal/${symbols[0]}`, { interval, mode });
    }
    // Otherwise use the multi-symbol endpoint
    params.symbols = symbols.join(',');
  }
  
  return useApi('/signals', params);
}

/**
 * Get market data with indicators for a specific symbol and timeframe
 * @param {string} symbol - Cryptocurrency symbol (e.g., BTCUSDT)
 * @param {string} interval - Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
 * @param {number} limit - Number of candles to fetch
 * @returns {Object} - { data, loading, error, refetch }
 */
export const useMarketData = (symbol, interval = '1h', limit = 100) => {
  return useApi(`/marketdata/${symbol}`, { interval, limit })
}

/**
 * Get list of watched symbols
 * @returns {Object} - { data, loading, error, refetch }
 */
export const useSymbols = () => {
  return useApi('/symbols')
}